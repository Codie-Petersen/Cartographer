import numpy as np
import math
import time
import os
import msvcrt        
import random


class Player:
    def __init__(self, x, y, z):
        self.position = np.array([x, y, z])
        self.color = '\033[92m'  # ANSI escape code for green color

    def get_char(self):
        # Determine character based on z position
        if self.position[2] > 10:
            return '.'
        elif self.position[2] > -10:
            return '•'
        else:
            return '▲'

    def move(self, dx, dy, dz):
        self.position += np.array([dx, dy, dz])

    def rotate(self, rotation_matrix, rotation_center):
        translated = self.position - rotation_center
        rotated = np.dot(rotation_matrix, translated)
        self.position = rotated + rotation_center

    def get_projected_position(self, width, height, fov):
        x, y, z = self.position
        z = max(z, 0.1)  # Ensure z is positive
        perspective = fov / (fov + z)
        x_proj = int((x * perspective * 2) + (width / 2))  # Multiply by 2 to account for character aspect ratio
        y_proj = int((y * perspective) + (height / 2))
        return max(0, min(x_proj, width - 1)), max(0, min(y_proj, height - 1))

class Star:
    def __init__(self, position):
        self.position = np.array(position)
        self.name = self.generate_name()
        self.type = random.choice(['Red Dwarf', 'Yellow Dwarf', 'White Dwarf', 'Blue Giant', 'Red Giant'])
        self.temperature = random.randint(3000, 30000)  # in Kelvin
        self.size = random.uniform(0.1, 100)  # in solar radii
        self.age = random.uniform(0.1, 10)  # in billions of years

    def rotate(self, rotation_matrix, rotation_center):
        translated = self.position - rotation_center
        rotated = np.dot(rotation_matrix, translated)
        self.position = rotated + rotation_center

    @staticmethod
    def generate_name():
        prefixes = ['Alpha', 'Beta', 'Gamma', 'Delta', 'Epsilon']
        suffixes = ['Centauri', 'Cygni', 'Eridani', 'Draconis', 'Lyrae']
        return f"{random.choice(prefixes)} {random.choice(suffixes)} {random.randint(1, 999)}"

    def get_info(self):
        return f"Name: {self.name} | Type: {self.type} | Temp: {self.temperature}K | Size: {self.size:.2f} solar radii | Age: {self.age:.2f} billion years"
        
class StarField:
    def __init__(self, num_stars, width, height, fov, field_size=30):
        self.field_size = field_size
        self.stars = [
            Star(np.random.uniform(-self.field_size/2, self.field_size/2, 3))
            for _ in range(num_stars)
        ]
        self.width = width
        self.height = height
        self.fov = fov
        self.rotation_center = np.array([0, 0, 0])
        self.star_chars = '.•*'

    def generate_stars(self):
        return [
            Star(np.random.uniform(-self.field_size/2, self.field_size/2, 3))
            for _ in range(len(self.stars))
        ]
        
    def rotate_stars(self, angle_x, angle_y, angle_z):
        rotation_x = np.array([
            [1, 0, 0],
            [0, np.cos(angle_x), -np.sin(angle_x)],
            [0, np.sin(angle_x), np.cos(angle_x)]
        ])
        rotation_y = np.array([
            [np.cos(angle_y), 0, np.sin(angle_y)],
            [0, 1, 0],
            [-np.sin(angle_y), 0, np.cos(angle_y)]
        ])
        rotation_z = np.array([
            [np.cos(angle_z), -np.sin(angle_z), 0],
            [np.sin(angle_z), np.cos(angle_z), 0],
            [0, 0, 1]
        ])
        rotation_matrix = np.dot(rotation_z, np.dot(rotation_y, rotation_x))
        for star in self.stars:
            star.rotate(rotation_matrix, self.rotation_center)

    def project_stars(self):
        projected_stars = []
        aspect_ratio = 2  # Characters are typically twice as tall as they are wide
        for star in self.stars:
            x, y, z = star.position
            # Ensure z is always positive for projection
            z = max(z, 0.1)  # Avoid division by zero
            # Calculate perspective
            perspective = self.fov / (self.fov + z)
            # Adjust x projection to account for character aspect ratio
            x_proj = (x * perspective * aspect_ratio) + (self.width / 2)
            y_proj = (y * perspective) + (self.height / 2)
            # Scale to fit within screen bounds
            x_proj = max(0, min(x_proj, self.width - 1))
            y_proj = max(0, min(y_proj, self.height - 1))
            distance = np.sqrt(x**2 + y**2 + z**2)
            projected_stars.append((int(x_proj), int(y_proj), distance))
        return projected_stars
        
    def get_star_char(self, distance):
        max_distance = self.field_size * np.sqrt(3)  # Maximum possible distance in the cube
        normalized_distance = distance / max_distance
        
        # Create more gradual thresholds for star characters
        if normalized_distance < 0.1:
            return '*'
        elif normalized_distance < 0.25:
            return '•'
        elif normalized_distance < 0.5:
            return '·'
        else:
            return '.'

    def render(self):
        projected_stars = self.project_stars()
        output = np.full((self.height, self.width), ' ')
        for x, y, distance in projected_stars:
            output[y, x] = self.get_star_char(distance)
        return '\n'.join([''.join(row) for row in output])

class StarFieldSimulator:
    def __init__(self, width, height, num_stars, fov, field_size=30):
        self.star_field = StarField(num_stars, width, height, fov, field_size)
        self.angle_x = self.angle_y = self.angle_z = 0
        self.player = Player(0, 0, 0)  # Start the player in center of the star field
        self.width = width
        self.height = height
        self.fov = fov

    def handle_input(self):
        if msvcrt.kbhit():
            key = msvcrt.getch()
            if key == b'\xe0':  # Arrow key prefix
                key = msvcrt.getch()
                if key == b'H':  # Up arrow
                    self.player.move(0, -1, 0)
                elif key == b'P':  # Down arrow
                    self.player.move(0, 1, 0)
                elif key == b'K':  # Left arrow
                    self.player.move(-1, 0, 0)
                elif key == b'M':  # Right arrow
                    self.player.move(1, 0, 0)
            else:
                key = key.decode('utf-8').lower()
                if key == 'w':
                    self.angle_x -= 0.1
                elif key == 's':
                    self.angle_x += 0.1
                elif key == 'a':
                    self.angle_y -= 0.1
                elif key == 'd':
                    self.angle_y += 0.1
                elif key == 'q':
                    self.angle_z -= 0.1
                elif key == 'e':
                    self.angle_z += 0.1
            return True
        return False

    def clear_rotation_speed(self):
        self.angle_x = 0.0
        self.angle_y = 0.0
        self.angle_z = 0.0

    def update(self):
        rotation_x = np.array([
            [1, 0, 0],
            [0, np.cos(self.angle_x), -np.sin(self.angle_x)],
            [0, np.sin(self.angle_x), np.cos(self.angle_x)]
        ])
        rotation_y = np.array([
            [np.cos(self.angle_y), 0, np.sin(self.angle_y)],
            [0, 1, 0],
            [-np.sin(self.angle_y), 0, np.cos(self.angle_y)]
        ])
        rotation_z = np.array([
            [np.cos(self.angle_z), -np.sin(self.angle_z), 0],
            [np.sin(self.angle_z), np.cos(self.angle_z), 0],
            [0, 0, 1]
        ])
        rotation_matrix = np.dot(rotation_z, np.dot(rotation_y, rotation_x))
        
        self.star_field.rotate_stars(self.angle_x, self.angle_y, self.angle_z)
        self.player.rotate(rotation_matrix, self.star_field.rotation_center)
        
    def find_nearest_star(self):
        player_pos = self.player.position
        distances = [np.linalg.norm(star.position - player_pos) for star in self.star_field.stars]
        nearest_index = np.argmin(distances)
        return self.star_field.stars[nearest_index], distances[nearest_index]

    def render(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        star_field = self.star_field.render()
        lines = star_field.split('\n')
        player_x, player_y = self.player.get_projected_position(self.width, self.height, self.fov)
        player_char = self.player.get_char()

        for i, char_line in enumerate(player_char.split('\n')):
            if 0 <= player_y + i < len(lines):
                line = lines[player_y + i]
                new_line = line[:player_x] + self.player.color + char_line + '\033[0m' + line[player_x+len(char_line):]
                lines[player_y + i] = new_line

        print('\n'.join(lines))
        
        nearest_star, distance = self.find_nearest_star()
        print(f"Ship Position: {self.player.position[0]:.2f}:{self.player.position[1]:.2f}:{self.player.position[2]:.2f}")
        print(f"Nearest Star (Distance: {distance:.2f}): {nearest_star.get_info()}")

    def run(self):
        #First update.
        self.update()
        self.render()
        while True:
            update = self.handle_input()
            if update:
                self.update()
                self.render()
                self.clear_rotation_speed()
                time.sleep(0.05)

if __name__ == "__main__":
    simulator = StarFieldSimulator(width=128, height=64, num_stars=150, fov=120)
    simulator.run()