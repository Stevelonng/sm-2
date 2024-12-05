from datetime import datetime, timedelta


class AnkiStyleSM2:
    def __init__(self):
        self.initial_ease = 2.5
        self.minimum_ease = 1.3
        self.interval_modifier = 1.0

        # Learning steps in minutes
        self.learning_steps = [1, 10]
        self.graduating_interval = 1  # day
        self.easy_interval = 4  # days

        # Interval modifiers
        self.hard_interval_modifier = 1.2
        self.easy_interval_modifier = 1.3

        # Ease factor adjustments
        self.ease_hard = 0.15
        self.ease_good = 0.0
        self.ease_easy = 0.15
        self.ease_again = 0.2

    def calculate_next_review(self, repetition, ease_factor, last_interval, quality):
        """Calculate next review time using properly differentiated Anki-style scheduling"""
        current_time = datetime.now()

        # New card or in learning phase
        if repetition < len(self.learning_steps):
            if quality == 0:  # Again
                repetition = 0
                interval = self.learning_steps[0] / (24 * 60)  # 1 minute
                ease_factor = max(self.minimum_ease, ease_factor - self.ease_again)

            elif quality == 1:  # Hard
                # Stay at current step
                interval = self.learning_steps[repetition] / (24 * 60)
                ease_factor = max(self.minimum_ease, ease_factor - self.ease_hard)

            elif quality == 2:  # Good
                repetition += 1
                if repetition < len(self.learning_steps):
                    interval = self.learning_steps[repetition] / (24 * 60)  # 10 minutes
                else:
                    interval = self.graduating_interval  # 1 day

            else:  # Easy (3)
                repetition = len(self.learning_steps)  # Graduate immediately
                interval = self.easy_interval  # 4 days
                ease_factor = min(ease_factor + self.ease_easy, 3.0)

        # Graduated card
        else:
            if quality == 0:  # Again
                repetition = 0
                interval = self.learning_steps[0] / (24 * 60)  # Back to 1 minute
                ease_factor = max(self.minimum_ease, ease_factor - self.ease_again)

            elif quality == 1:  # Hard
                interval = last_interval * self.hard_interval_modifier  # 1.2x current interval
                ease_factor = max(self.minimum_ease, ease_factor - self.ease_hard)

            elif quality == 2:  # Good
                interval = last_interval * ease_factor

            else:  # Easy (3)
                interval = last_interval * ease_factor * self.easy_interval_modifier
                ease_factor = min(ease_factor + self.ease_easy, 3.0)

        # Calculate next review time
        if interval < 1:  # Less than a day
            next_review = current_time + timedelta(minutes=int(interval * 24 * 60))
        else:
            next_review = current_time + timedelta(days=int(interval))

        return {
            'repetition': repetition,
            'ease_factor': ease_factor,
            'interval': interval,
            'next_review': next_review
        }

    def review_card(self, card_state, quality):
        if not card_state:
            card_state = {
                'repetition': 0,
                'ease_factor': self.initial_ease,
                'interval': 0,
                'next_review': datetime.now()
            }

        return self.calculate_next_review(
            card_state['repetition'],
            card_state['ease_factor'],
            card_state['interval'],
            quality
        )