import os
import json
import numpy as np

from ursina import *
from ursina.prefabs.dropdown_menu import DropdownMenu, DropdownMenuButton

from numba import jit, prange

from typing import *

app = Ursina()

window.title = 'Particle Life'
window.exit_button.enabled = False
window.size = Vec2(2000, 1250)
window.color = color.black

window.center_on_screen()
scene.camera.orthographic = True

X_WINDOW_RANGE = -30.0, 30.0
Y_WINDOW_RANGE = -15.0, 15.0


"""
PRESETS = attraction_matrix = np.array([[-0.0288, -0.0445, -0.0145, 0.0036], [0.0201, -0.0212, 0.1622, 0.0383],
                                        [-0.0038, 0.0315, -0.0382, -0.0162],[0.0110, -0.0199, 0.0483, -0.0469]])
"""


COLORS = list(color.colors.values())


class Particle(Entity):

    def __init__(self, x: float, y: float, ptype: int=0):
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

    def __init__(self, num_types: int, particles_per_type: int, attract_mean: float, attract_std: float,
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

        self.particle_matrix = []
        self.attraction_matrix = []
        self.min_r_matrix = []
        self.max_r_matrix = []

    def construct_particle_matrix(self):
        self.particle_matrix = []
        for particle in self.particles:
            self.particle_matrix.append([particle.x, particle.y, particle.vx, particle.vy, particle.ptype])

    def construct_matricies(self):
        self.attraction_matrix = []
        self.min_r_matrix = []
        self.max_r_matrix = []
        for _ in range(self.num_types):
            self.attraction_matrix.extend(
                [[random.uniform(self.attract_mean, self.attract_std) for _ in range(self.num_types)]])
            self.min_r_matrix.extend(
                [[random.uniform(self.min_r_lower, self.min_r_upper) for _ in range(self.num_types)]])
            self.max_r_matrix.extend(
                [[random.uniform(self.max_r_lower, self.max_r_upper) for _ in range(self.num_types)]])

    def get_attraction(self, ptype1: int, ptype2: int) -> float:
        return self.attraction_matrix[ptype1][ptype2]

    def get_min_r(self, ptype1: int, ptype2: int) -> float:
        return self.min_r_matrix[ptype1][ptype2]

    def get_max_r(self, ptype1: int, ptype2: int) -> float:
        return self.max_r_matrix[ptype1][ptype2]

    def init(self):
        self.particles = []
        self.construct_matricies()
        for i in range(self.num_types):
            for _ in range(self.particles_per_type):
                self.particles.append(Particle(random.uniform(*X_WINDOW_RANGE),
                                               random.uniform(*Y_WINDOW_RANGE),
                                               ptype=i))
        self.construct_particle_matrix()

        self.particle_matrix = np.array(self.particle_matrix)
        self.attraction_matrix = np.array(self.attraction_matrix)
        self.min_r_matrix = np.array(self.min_r_matrix)
        self.max_r_matrix = np.array(self.max_r_matrix)

    def re_init_particles(self):
        for particle in self.particles:
            particle.enabled = False

        self.particles = []
        for i in range(self.num_types):
            for _ in range(self.particles_per_type):
                self.particles.append(Particle(random.uniform(*X_WINDOW_RANGE),
                                               random.uniform(*Y_WINDOW_RANGE),
                                               ptype=i))
        self.construct_particle_matrix()

    def reset(self):
        for particle in self.particles:
            particle.enabled = False
            del particle
        self.init()

    @staticmethod
    @jit(parallel=True)
    def numba_step_compute(particle_matrix: List, attraction_matrix: List,
                           min_r_matrix: List, max_r_matrix: List, friction: float):

        for i in range(len(particle_matrix)):
            particle = particle_matrix[i]

            for n in prange(len(particle_matrix)):
                q = particle_matrix[n]

                particle_ptype = int(particle[-1])
                q_pype = int(q[-1])

                dx = q[0] - particle[0]
                dy = q[1] - particle[1]

                r2 = dx ** 2 + dy ** 2
                min_r = min_r_matrix[particle_ptype][q_pype]
                max_r = max_r_matrix[particle_ptype][q_pype]

                if r2 > max_r ** 2 or r2 < 0.01:
                    continue

                r = np.sqrt(r2)
                dx /= r
                dy /= r

                if r > min_r:
                    numer = 2.0 * np.abs(r - 0.5 * (max_r + min_r))
                    denom = max_r - min_r
                    f = attraction_matrix[particle_ptype][q_pype] * (1.0 - numer / denom)
                else:
                    r_smooth = 2.0
                    f = r_smooth * min_r * (1.0 / (min_r + r_smooth) - 1.0 / (r + r_smooth))

                particle[2] += f * dx
                particle[3] += f * dy

            particle_matrix[i] = particle

        for i in prange(len(particle_matrix)):
            particle = particle_matrix[i]

            particle[0] += particle[2] * 0.1  # Velocity
            particle[1] += particle[3] * 0.1  # Velocity

            particle[2] *= 1.0 - friction
            particle[3] *= 1.0 - friction

            if particle[0] >= 35 or particle[0] <= -35:
                particle[2] *= -1.5  # Bounce back

            if particle[1] >= 20 or particle[1] <= -20:
                particle[3] *= -1.5  # Bounce back

            particle_matrix[i] = particle

        return particle_matrix

    def step(self):
        self.particle_matrix = self.numba_step_compute(self.particle_matrix, self.attraction_matrix,
                                                       self.min_r_matrix, self.max_r_matrix, self.friction)

        for coords, particle_ in zip(self.particle_matrix, self.particles):
            particle_.x = coords[0]
            particle_.y = coords[1]

    def save_settings(self, file_path: str='particle-life-presets/settings'):
        settings = json.dumps({
            'num_types': self.num_types,
            'particles_per_type': self.particles_per_type,
            'attraction_matrix': self.attraction_matrix.tolist(),
            'min_r_matrix': self.min_r_matrix.tolist(),
            'max_r_matrix': self.max_r_matrix.tolist(),
            'friction': self.friction
        }, indent=4)

        if file_path.count('/') == 0:
            directory = os.getcwd()

            for i, file in enumerate(os.listdir(directory)):
                if os.path.isfile(directory + '/' + file_path):
                    if i < 1:
                        file_path += str(i)
                    else:
                        file_path = list(file_path)
                        file_path[-1] = str(i)
                        file_path = ''.join(file_path)
        else:
            directory = file_path[:file_path.rfind('/')]
            if os.path.exists(directory):
                for i, file in enumerate(os.listdir(directory)):
                    if os.path.isfile(directory + '/' + file_path):
                        if i < 1:
                            file_path += str(i)
                        else:
                            file_path = list(file_path)
                            file_path[-1] = str(i)
                            file_path = ''.join(file_path)
            else:
                os.mkdir(os.getcwd() + '/' + directory)

        with open(file_path, 'w') as f:
            f.write(settings)

    def load_settings(self, file_path: str):
        with open(file_path, 'r') as f:
            settings = json.load(f)

            not_arrays = ['num_types', 'friction', 'particles_per_type']
            for name in not_arrays:
                self.__setattr__(name, settings[name])
                del settings[name]

            self.reset()
            for name, value in settings.items():
                self.__setattr__(name, np.array(value))


def update():
    universe.step()


def reset():
    universe.reset()


def load_cells1():
    universe.load_settings('presets/cells-1.json')


def load_cells2():
    universe.load_settings('presets/cells-2.json')


def load_hunting_green_blobs():
    universe.load_settings('presets/hunting-green-blobs.json')


def load_ecosystem1():
    universe.load_settings('presets/ecosystem-1.json')


def run():
    global universe
    universe = Universe(num_types=12,
                        particles_per_type=50,
                        attract_mean=-0.05,
                        attract_std=0.05,
                        min_r_lower=0.5,
                        min_r_upper=1,
                        max_r_lower=-10,
                        max_r_upper=10,
                        friction=0.1)
    universe.init()

    Button(model=Quad(scale=(1, 0.5)), text='Reset', scale=0.1,
           color=color.azure, x=window.top_left[0], y=0.45, on_click=reset)

    drop_down = DropdownMenu('Presets', buttons=(
        DropdownMenuButton('Cells 1', on_click=load_cells1),
        DropdownMenuButton('Cells 2', on_click=load_cells2),
        DropdownMenuButton('Hunting Green Blobs', on_click=load_hunting_green_blobs),
        DropdownMenuButton('Ecosystem 1', on_click=load_ecosystem1)
    ), color=color.azure, x=window.top_left[0] + 0.1, y=0.46)

    drop_down.arrow_symbol.color = color.white

    app.run()


if __name__ == '__main__':
    run()
