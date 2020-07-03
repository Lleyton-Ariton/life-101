import numpy as np

from ursina import *

# from numba import jit

# from typing import *

app = Ursina()

window.exit_button.enabled = False
window.size = Vec2(2000, 1250)
window.color = color.black

window.center_on_screen()

X_WINDOW_RANGE = -30.0, 30.0
Y_WINDOW_RANGE = -15.0, 15.0

TICKER = 0
NUM_PARTICLES = 100

COLORS = list(color.colors.values())


class Particle(Entity):

    def __init__(self, x: float, y: float, ptype: int = 0):
        super().__init__(model=Circle(16), color=color.green, scale=0.5)
        self.x = x
        self.y = y

        self.vx = 0
        self.vy = 0

        self.ptype = ptype
        self.color = COLORS[self.ptype + 6]

    def __str__(self) -> str:
        return str(self.__dict__)


class Universe:

    def __init__(self, num_types: int, particles_per_type: int, attract_mean: float,
                 attract_std: float,
                 min_r_lower: float, min_r_upper: float, max_r_lower: float, max_r_upper: float,
                 friction: float, flat_force: bool = False, wrap: bool = False):
        self.num_types = num_types + 1
        self.particles_per_type = particles_per_type
        self.attract_mean = attract_mean
        self.attract_std = attract_std
        self.min_r_lower = min_r_lower
        self.min_r_upper = min_r_upper
        self.max_r_lower = max_r_lower
        self.max_r_upper = max_r_upper
        self.friction = friction
        self.flat_force = flat_force
        self.wrap = wrap

        self.particles = []

        self.width = window.size[0]
        self.height = window.size[1]

        self.attraction_matrix = []
        self.min_r_matrix = []
        self.max_r_matrix = []

    def construct_matricies(self):
        self.attraction_matrix = []
        self.min_r_matrix = []
        self.max_r_matrix = []
        for _ in range(self.num_types):
            self.attraction_matrix.extend([[random.uniform(self.attract_mean, self.attract_std) for
                                            _ in range(self.num_types)]])
            self.min_r_matrix.extend([[random.uniform(self.min_r_lower, self.min_r_upper) for _ in
                                       range(self.num_types)]])
            self.max_r_matrix.extend([[random.uniform(self.max_r_lower, self.max_r_upper) for _ in
                                       range(self.num_types)]])

    def get_attraction(self, ptype1: int, ptype2: int) -> float:
        return self.attraction_matrix[ptype1][ptype2]

    def get_min_r(self, ptype1: int, ptype2: int) -> float:
        return self.min_r_matrix[ptype1][ptype2]

    def get_max_r(self, ptype1: int, ptype2: int) -> float:
        return self.max_r_matrix[ptype1][ptype2]

    def init(self):
        self.construct_matricies()
        for i in range(self.num_types):
            for _ in range(self.particles_per_type):
                self.particles.append(Particle(random.uniform(*X_WINDOW_RANGE),
                                               random.uniform(*Y_WINDOW_RANGE),
                                               ptype=i))

    """
    @staticmethod
    @jit(nopython=True, parallel=True)
    def numba_force_compute(r2: float, attraction: float, min_r: float, max_r: float):
        r = np.sqrt(r2)

        if r > min_r:
            numer = 2.0 * np.abs(r - 0.5 * (max_r + min_r))
            denom = max_r - min_r
            f = attraction * (1.0 - numer / denom)
        else:
            r_smooth = 2.0
            f = r_smooth * min_r * (1.0 / (min_r + r_smooth) - 1.0 / (r + r_smooth))

        return f
    """

    def step(self):
        for i, particle in enumerate(self.particles):
            for q in self.particles:

                dx = q.x - particle.x
                dy = q.y - particle.y

                r2 = dx ** 2 + dy ** 2
                min_r = self.get_min_r(particle.ptype, q.ptype)
                max_r = self.get_max_r(particle.ptype, q.ptype)

                if r2 > max_r ** 2 or r2 < 0.01:
                    continue

                r = np.sqrt(r2)
                dx /= r
                dy /= r

                if r > min_r:
                    numer = 2.0 * np.abs(r - 0.5 * (max_r + min_r))
                    denom = max_r - min_r
                    f = self.get_attraction(particle.ptype, q.ptype) * (1.0 - numer / denom)
                else:
                    r_smooth = 2.0
                    f = r_smooth * min_r * (1.0 / (min_r + r_smooth) - 1.0 / (r + r_smooth))

                """
                f = self.numba_force_compute(r2=r2,
                                             attraction=self.get_attraction(particle.ptype, q.ptype),
                                             min_r=min_r, max_r=max_r)
                """

                particle.vx += f * dx
                particle.vy += f * dy

            self.particles[i] = particle

        for i, particle in enumerate(self.particles):
            particle.x += particle.vx * 0.1  # Velocity
            particle.y += particle.vy * 0.1  # Velocity

            particle.vx *= 1.0 - self.friction
            particle.vy *= 1.0 - self.friction

            if particle.x >= 35 or particle.x <= -35:
                particle.vx *= -1

            if particle.y >= 20 or particle.y <= -20:
                particle.vy *= -1

            self.particles[i] = particle


def update():
    universe.step()


def run():
    scene.camera.orthographic = True

    global universe
    universe = Universe(num_types=5,
                        particles_per_type=30,
                        attract_mean=-0.05,
                        attract_std=0.05,
                        min_r_lower=0.5,
                        min_r_upper=1,
                        max_r_lower=-10,
                        max_r_upper=10,
                        friction=0.1)
    universe.init()

    app.run()


if __name__ == '__main__':
    run()
