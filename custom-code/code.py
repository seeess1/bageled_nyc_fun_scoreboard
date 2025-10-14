import time
import board
import digitalio
import displayio
from adafruit_matrixportal.matrix import Matrix
from adafruit_display_text import label
import terminalio

from adafruit_seesaw.digitalio import DigitalIO
from adafruit_seesaw.pwmout import PWMOut
from adafruit_seesaw.seesaw import Seesaw

turn_on = True

# ===============================
# Opponents
# ===============================
matchups = [
    {
        "top_name": "PLAIN",
        "top_short": "PLAIN",
        "top_color": 0xFF4500,
        "bottom_name": "SCALLION",
        "bottom_short": "SCLN",
        "bottom_color": 0x1E90FF,
    }
]

# Active matchup state
current_match_index = 0
top_opponent_name = {}
bottom_opponent_name = {}
top_opponent_label_color = 0x0eff00
bottom_opponent_label_color = 0x0006ff
bageled_label_color = 0xE7F23C


# ===============================
# Helpers
# ===============================
def load_matchup(index):
    """Load opponent names/colors from matchups list."""
    global top_opponent_name, bottom_opponent_name
    global sets_completed, games_top, games_bottom

    print("Loading matchup!")

    matchup = matchups[index]

    top_opponent_name = {matchup["top_short"]: matchup["top_name"]}
    bottom_opponent_name = {matchup["bottom_short"]: matchup["bottom_name"]}

    # Reset match state
    sets_completed = []
    games_top = 0
    games_bottom = 0

    print(f"top_opponent_name: {top_opponent_name}")
    print(f"bottom_opponent_name: {bottom_opponent_name}")

# ===============================
# Display setup
# ===============================
matrix = Matrix(width=64, height=32, bit_depth=1)
display = matrix.display
label_scale = 1
font = terminalio.FONT

main_group = displayio.Group()
display.root_group = main_group

# ===============================
# Seesaw + Buttons setup
# ===============================
i2c = board.STEMMA_I2C()
arcade_qt = Seesaw(i2c, addr=0x3A)

button_up = DigitalIO(arcade_qt, 18)
button_up.direction = digitalio.Direction.INPUT
button_up.pull = digitalio.Pull.UP

button_down = DigitalIO(arcade_qt, 19)
button_down.direction = digitalio.Direction.INPUT
button_down.pull = digitalio.Pull.UP

led_up = PWMOut(arcade_qt, 12)
led_down = PWMOut(arcade_qt, 13)

led_up.duty_cycle = 0
led_down.duty_cycle = 0

# ===============================
# Tennis scoring state
# ===============================
sets_completed = []
games_top = 0
games_bottom = 0

def show_message(text, duration=2):
    """Display a single message centered on the LED for `duration` seconds."""
    while len(main_group) > 0:
        main_group.pop()

    msg_label = label.Label(
        font=font,
        text=text,
        scale=label_scale
    )
    msg_label.anchor_point = (0.5, 0.5)  # center
    msg_label.anchored_position = (display.width // 2, display.height // 2)

    main_group.append(msg_label)
    time.sleep(duration)


def show_message_two_lines(
        line1, 
        line2, 
        duration=3, 
        line1_color=0xFFFFFF, 
        line2_color=0xFFFFFF
        ):
    """Display a two-line centered message."""
    while len(main_group) > 0:
        main_group.pop()

    # First line
    label1 = label.Label(
        font=font,
        text=line1,
        scale=label_scale,
        color=line1_color
    )
    label1.anchor_point = (0.5, 1)  # bottom-center of the top half
    label1.anchored_position = (display.width // 2, display.height // 2)

    # Second line
    label2 = label.Label(
        font=font,
        text=line2,
        scale=label_scale,
        color=line2_color
    )
    label2.anchor_point = (0.5, 0)  # top-center of the bottom half
    label2.anchored_position = (display.width // 2, display.height // 2)

    main_group.append(label1)
    main_group.append(label2)

    time.sleep(duration)


# ===============================
# Drawing functions
# ===============================
def redraw_scores():
    score_left_anchor_pixel = 35
    """Redraw the scoreboard with names (left-aligned) and scores"""
    while len(main_group) > 0:
        main_group.pop()

    group = displayio.Group()

    # Start with completed sets (in order)
    top_scores = ""
    bottom_scores = ""
    for t, n in sets_completed:
        top_scores += f"{t} "
        bottom_scores += f"{n} "

    # Then add the *current games* at the end
    top_scores += f"{games_top}"
    bottom_scores += f"{games_bottom}"

    # --- Top row: ---
    top_name_label = label.Label(font, text=next(iter(top_opponent_name)),
                               color=top_opponent_label_color, scale=label_scale)
    top_name_label.anchor_point = (0, 0)   # left aligned, top
    top_name_label.anchored_position = (0, 0)

    top_score_label = label.Label(font, text=top_scores,
                                color=top_opponent_label_color, scale=label_scale)
    top_score_label.anchor_point = (0, 0)   # left aligned at score anchor
    top_score_label.anchored_position = (score_left_anchor_pixel, 0)

    # --- Bottom row: ---
    bottom_name_label = label.Label(font, text=next(iter(bottom_opponent_name)),
                                   color=bottom_opponent_label_color, scale=label_scale)
    bottom_name_label.anchor_point = (0, 1)  # left aligned, bottom
    bottom_name_label.anchored_position = (0, display.height)

    bottom_score_label = label.Label(font, text=bottom_scores,
                                    color=bottom_opponent_label_color, scale=label_scale)
    bottom_score_label.anchor_point = (0, 1)  # left aligned, bottom
    bottom_score_label.anchored_position = (score_left_anchor_pixel, display.height)

    # Add everything to the group
    group.append(top_name_label)
    group.append(top_score_label)
    group.append(bottom_name_label)
    group.append(bottom_score_label)

    main_group.append(group)


def flash_bageled():
    """Flash 'Bageled!' three times in the center of the screen."""
    flash_label = label.Label(
        font=font,
        text="Bageled!",
        color=bageled_label_color,
        scale=label_scale
    )
    flash_label.anchor_point = (0.5, 0.5)
    flash_label.anchored_position = (display.width // 2, display.height // 2)

    # Save current children to restore later
    saved_children = list(main_group)
    while len(main_group) > 0:
        main_group.pop()

    for _ in range(3):
        main_group.append(flash_label)
        time.sleep(1)
        main_group.pop()
        time.sleep(0.25)

    for child in saved_children:
        main_group.append(child)

def wait_for_button_press():
    """Block until either button_up or button_down is pressed."""
    while True:
        if not button_up.value or not button_down.value:
            return
        time.sleep(0.05)

def check_match_completed(sets_completed_list):
    global current_match_index

    print("Checking if match is complete...")
    top_sets_won = sum(1 for t, b in sets_completed_list if t > b)
    bottom_sets_won = sum(1 for t, b in sets_completed_list if b > t)

    if (top_sets_won == 1) and (bottom_sets_won == 1):
        print("Match not complete yet")
        return

    if top_sets_won > 1:
        winner_name = next(iter(top_opponent_name.values()))
        winner_label_color = top_opponent_label_color
    elif bottom_sets_won > 1:
        winner_name = next(iter(bottom_opponent_name.values()))
        winner_label_color = bottom_opponent_label_color
    else:
        return

    print("Match complete! Just waiting for button press to start new match!")
    # Display winner until someone presses a button
    while True:
        show_message_two_lines(
            line1=winner_name,
            line2="WINS!",
            line1_color=winner_label_color,
            duration=2,
        )
        if not button_up.value or not button_down.value:
            # Wait for release before continuing
            while not button_up.value or not button_down.value:
                time.sleep(0.05)
            break

    # Advance to next matchup (loop around if needed)
    current_match_index = (current_match_index + 1) % len(matchups)
    load_matchup(current_match_index)

    # Run intro again before next match
    redraw_scores()


def check_set_completion():
    """Check if a set has ended and handle completion/reset."""
    global games_top, games_bottom, sets_completed

    top = games_top
    bottom = games_bottom

    if ((top >= 6 or bottom >= 6) and abs(top - bottom) >= 2) or \
       (top == 7 and bottom == 6) or (top == 6 and bottom == 7):
        print("Set completed!")
        sets_completed.append((top, bottom))
        print(f"New sets_completed list: {sets_completed}")

        # Flash if bagel
        if (top == 6 and bottom == 0) or (top == 0 and bottom == 6):
            flash_bageled()

        games_top = 0
        games_bottom = 0

        # Check if the match is done
        if len(sets_completed) > 1:
            check_match_completed(sets_completed)


# ===============================
# Main loop
# ===============================
print("Scoreboard ready!")
load_matchup(0)
redraw_scores()

duty_cycle = 65535

while turn_on:
    if not button_up.value:  # Top scores
        games_top += 1
        check_set_completion()
        redraw_scores()
        led_up.duty_cycle = duty_cycle
        time.sleep(0.3)
    else:
        led_up.duty_cycle = 0

    if not button_down.value:  # Bottom scores
        games_bottom += 1
        check_set_completion()
        redraw_scores()
        led_down.duty_cycle = duty_cycle
        time.sleep(0.3)
    else:
        led_down.duty_cycle = 0

    time.sleep(0.05)
