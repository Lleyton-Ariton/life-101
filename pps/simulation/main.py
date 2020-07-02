import numpy as np

from ursina import *
from numba import jit

from typing import *

app = Ursina()

window.exit_button.enabled = False
window.size = Vec2(2000, 1250)
window.color = color.black

window.center_on_screen()

# X_WINDOW_RANGE = -35.0, 35.0
# Y_WINDOW_SIZE = -20.0, 20.0

X_WINDOW_RANGE = -30.0, 30.0
Y_WINDOW_SIZE = -15.0, 15.0

TICKER = 0
RADIUS = 2.5
VELOCITY = 0.25
ALPHA = 180
BETA = 100
NUM_PARTICLES = 500

ALPHA = np.radians(ALPHA)
BETA = np.radians(BETA)


class Particle(Entity):

    def __init__(self, x: float, y: float):
        super().__init__(model=Circle(16), color=color.green, scale=0.5)
        self.x = x
        self.y = y

        self.phi = 0

    def update_phi(self, radians: float):
        self.phi += radians
        self.phi = self.phi % np.radians(360)


def construct_particle_array(all_particles: List[Particle]):
    array = []
    for particle in all_particles:
        array.append([particle.x, particle.y, particle.phi])
    return np.array(array)


def count_particles_in_hemispheres(particle: Particle) -> Tuple[int, int]:
    left = []
    right = []

    particle.color = color.green

    for other_particle in particles:
        if (particle.x - RADIUS) <= other_particle.x <= (particle.x + RADIUS):
            if particle.y <= other_particle.y <= (particle.y + RADIUS):
                left.append(other_particle)

            elif particle.y >= other_particle.y >= (particle.y - RADIUS):
                right.append(other_particle)

    n = len(left) + len(right)
    if n >= 35:
        particle.color = color.yellow
    elif 35 > n >= 20:
        particle.color = color.blue
    elif 20 > n > 10:
        particle.color = color.brown

    return len(left), len(right)


@jit(nopython=True, parallel=True)
def numba_particle_count(particle_coords: List[float], particle_array: np.ndarray, radius: float):
    left = []
    right = []

    for other_particle in particle_array:
        if (particle_coords[0] - radius) <= other_particle[0] <= (particle_coords[0] + radius):
            if particle_coords[1] <= other_particle[1] <= (particle_coords[1] + radius):
                left.append(other_particle)

            elif particle_coords[1] >= other_particle[1] >= (particle_coords[1] - radius):
                right.append(other_particle)

    return len(left), len(right)


def calculate_delta_phi(left: int, right: int, alpha: [int, float], beta: [int, float]) -> float:
    delta_phi = alpha + ((beta * (left + right)) * np.sign(right - left))
    return delta_phi


def move_particle(particle: Particle):
    particle.x += np.cos(particle.phi) * VELOCITY
    particle.y += np.sin(particle.phi) * VELOCITY

    particle.origin_x = particle.x
    particle.origin_y = particle.y


def update():
    global TICKER
    global RADIUS

    for i in range(len(particle_array_)):
        particle = particles[i]

        particle_count = numba_particle_count(particle_array_[i], particle_array_, RADIUS)
        particle.update_phi(calculate_delta_phi(*particle_count, ALPHA, BETA))

        n = sum(particle_count)
        if n >= 25:
            particle.color = color.yellow
        elif 20 > n >= 15:
            particle.color = color.blue
        elif 15 > n > 10:
            particle.color = color.brown
        else:
            particle.color = color.green

        move_particle(particle)
        particle_array_[i] = [particle.x, particle.y, particle.phi]

    """
    for particle in particles:
        particle.update_phi(calculate_delta_phi(*count_particles_in_hemispheres(particle), ALPHA, BETA))
        move_particle(particle)
    """

    TICKER += 1


def change_velocity():
    global VELOCITY
    VELOCITY = velocity_.value


def run_velocity_slider():
    velocity_.on_value_changed = change_velocity


def change_alpha():
    global ALPHA
    ALPHA = alpha_.value


def run_alpha_slider():
    alpha_.on_value_changed = change_alpha


def change_beta():
    global BETA
    BETA = beta_.value


def run_beta_slider():
    beta_.on_value_changed = change_beta


def change_radius():
    global RADIUS
    RADIUS = radius_.value


def run_radius_slider():
    radius_.on_value_changed = change_radius


def change_num_particles():
    global NUM_PARTICLES
    NUM_PARTICLES = num_particles_.value


def run_num_particles_slider():
    num_particles_.on_value_changed = change_num_particles


def reset():
    global particles
    global particle_array_

    for particle in particles:
        particle.enabled = False
        del particle
    particles = []

    for _ in range(int(NUM_PARTICLES)):
        particles.append(Particle(random.uniform(*X_WINDOW_RANGE), random.uniform(*Y_WINDOW_SIZE)))

    particle_array_ = construct_particle_array(particles)


if __name__ == '__main__':
    scene.camera.orthographic = True

    particles = []
    for _ in range(int(NUM_PARTICLES)):
        particles.append(Particle(random.uniform(*X_WINDOW_RANGE), random.uniform(*Y_WINDOW_SIZE)))

    particle_array_ = construct_particle_array(particles)

    velocity_ = ThinSlider(x=window.top_left[0], y=0.45, text='Velocity', dynamic=True, scale=0.5)
    run_velocity_slider()

    alpha_ = ThinSlider(x=window.top_left[0], y=0.40, text='Alpha', dynamic=True, scale=0.5, min=-180, max=180, step=0.1)
    run_alpha_slider()

    beta_ = ThinSlider(x=window.top_left[0], y=0.35, text='Beta', dynamic=True, scale=0.5, min=-180, max=180, step=0.1)
    run_beta_slider()

    radius_ = ThinSlider(x=window.top_left[0], y=0.30, text='Radius', dynamic=True, scale=0.5, min=0, max=10, step=0.1)
    run_radius_slider()

    num_particles_ = ThinSlider(x=window.top_left[0], y=0.25, text='Particles',
                                dynamic=True, scale=0.5, min=100, max=1000)
    run_num_particles_slider()

    reset_button = Button(model=Quad(scale=(1, 0.5)),
                          text='Reset', scale=0.1, color=color.azure, x=window.top_left[0], y=0.20, on_click=reset)

    app.run()
