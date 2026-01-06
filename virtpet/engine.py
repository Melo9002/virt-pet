import time
from virtpet.pet import Pet
from virtpet.persistence import save_pet

class GameEngine:
    def __init__(self, pet: Pet, minutes_per_real_second: float = 1.0):
        """
        :param minutes_per_real_second: how many in-game minutes pass per real second
        """
        self.pet = pet
        self.minutes_per_real_second = minutes_per_real_second
        self.running = True

        self._last_time = time.time()
        self._accumulated_minutes = 0.0

    def run(self):
        while self.running:
            now = time.time()
            delta = now - self._last_time
            self._last_time = now

            # Convert real time to game time
            self._accumulated_minutes += delta * self.minutes_per_real_second

            # Only tick whole minutes
            whole_minutes = int(self._accumulated_minutes)
            if whole_minutes > 0:
                self.pet.tick(whole_minutes)
                self._accumulated_minutes -= whole_minutes
                save_pet(self.pet)
            time.sleep(0.05)