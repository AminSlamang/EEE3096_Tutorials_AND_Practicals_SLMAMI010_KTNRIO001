# Import libraries
import RPi.GPIO as GPIO
import random
import ES2EEPROMUtils
import os
import time

# some global variables that need to change as we run the program
end_of_game = None  # set if the user wins or ends the game
guess_Value = 0
score =0
value = 0
buzzerSetting =0
# DEFINE THE PINS USED HERE
LED_value = [11, 13, 15]
LED_accuracy = 32
btn_submit = 16
btn_increase = 18
buzzer = 33
eeprom = ES2EEPROMUtils.ES2EEPROM()


# Print the game banner
def welcome():
    os.system('clear')
    print("  _   _                 _                  _____ _            __  __ _")
    print("| \ | |               | |                / ____| |          / _|/ _| |")
    print("|  \| |_   _ _ __ ___ | |__   ___ _ __  | (___ | |__  _   _| |_| |_| | ___ ")
    print("| . ` | | | | '_ ` _ \| '_ \ / _ \ '__|  \___ \| '_ \| | | |  _|  _| |/ _ \\")
    print("| |\  | |_| | | | | | | |_) |  __/ |     ____) | | | | |_| | | | | | |  __/")
    print("|_| \_|\__,_|_| |_| |_|_.__/ \___|_|    |_____/|_| |_|\__,_|_| |_| |_|\___|")
    print("")
    print("Guess the number and immortalise your name in the High Score Hall of Fame!")


# Print the game menu
def menu():
    global end_of_game
    end_of_game = False
    option = input("Select an option:   H - View High Scores     P - Play Game       Q - Quit\n")
    option = option.upper()
    if option == "H":
        os.system('clear')
        print("HIGH SCORES!!")
        s_count, ss = fetch_scores()
        display_scores(s_count, ss)
    elif option == "P":
        os.system('clear')
        print("Starting a new round!")
        print("Use the buttons on the Pi to make and submit your guess!")
        print("Press and hold the guess button to cancel your game")
        global value
        value = generate_number()
        global guess_Value
        guess_Value = 0 
        while not end_of_game:
            pass
    elif option == "Q":
        print("Come back soon!")
        exit()
    else:
        print("Invalid option. Please select a valid one!")


def display_scores(count, raw_data):
    # print the scores to the screen in the expected format
    print("There are {} scores. Here are the top 3!".format(count))
    # print out the scores in the required format
    if (count<3):
        for i in range(count):
            print("{} - {}{}{} took {} guesses".format((i+1), raw_data[i][0], raw_data[i][1], raw_data[i][2], raw_data[i][3]))
        less = 3 - count
        for i in range(less):
            print("{} - None".format((3-i)))
    else:
        for i in range(3):
            print("{} - {}{}{} took {} guesses".format((i+1), raw_data[i][0], raw_data[i][1], raw_data[i][2], raw_data[i][3]))




# Setup Pins
def setup():
    # Setup board mode
    GPIO.setmode(GPIO.BOARD)
    # Setup regular GPIO
    for i in LED_value:
        GPIO.setup(i,GPIO.OUT)
        GPIO.output(i,GPIO.LOW)
    GPIO.setup(btn_increase, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(btn_submit, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    # Setup PWM channels
    GPIO.setup(buzzer,GPIO.OUT)
    global Buzzer
    GPIO.output(buzzer,GPIO.LOW)
    Buzzer = GPIO.PWM(buzzer, 1000)
    GPIO.setup(LED_accuracy,GPIO.OUT)
    global AccuracyLED
    AccuracyLED = GPIO.PWM(LED_accuracy, 1000)
    AccuracyLED.start(0)
    # Setup debouncing and callbacks
    GPIO.add_event_detect(btn_increase, GPIO.FALLING, callback=btn_increase_pressed, bouncetime=300)
    GPIO.add_event_detect(btn_submit, GPIO.FALLING, callback=btn_guess_pressed, bouncetime=300)
    


# Load high scores
def fetch_scores():
    # get however many scores there are
    
    score_count = int((eeprom.read_block(0,1))[0])
    print(((eeprom.read_block(0,32))))
    print(((eeprom.read_block(1,32))))
    print(((eeprom.read_block(2,32))))
    print(((eeprom.read_block(3,32))))
    print(score_count)
    # Get the scores
    scores = []
    for i in range(score_count):
        scores.append(eeprom.read_block(i+1,4))
        for j in range(3):
            scores[i*4][j] = chr(scores[i*4][j])
            print(scores[i*4][j])
        scores[i*4][3] = int(scores[i*4][3])
    # convert the codes back to ascii
    
    # return back the results

    return score_count, scores


# Save high scores
def save_scores(name, score):
    # fetch scores
    # include new score
    # sort
    # update total amount of scores
    # write new scores
    score_count = int((eeprom.read_block(0,1))[0])
    scores = []
    nscores =[]
    for i in range(score_count):
        scores.append(eeprom.read_block(i+1,4))
        names = ""
        for j in range(3):
            names += chr(scores[i][j])
        nscores.append([names,int(scores[i][3])] )
    nscores.append([name,score])
    nscores.sort(key=lambda x: x[1])
    eeprom.write_block(0, [score_count+1])
    data_to_write = []
    for score in nscores:
        # get the string
        for letter in range(3):
            l = (score[0])[letter]
            data_to_write.append(ord(l))
        data_to_write.append(score[1])
    eeprom.write_block(1, data_to_write)

# Generate guess number
def generate_number():
    return random.randint(0, pow(2, 3)-1)


# Increase button pressed
def btn_increase_pressed(channel):
    # Increase the value shown on the LEDs
    # You can choose to have a global variable store the user's current guess, 
    # or just pull the value off the LEDs when a user makes a guess
    global guess_Value 
    guess_Value += 1
    if guess_Value >7 :
        guess_Value = 0
    temp = guess_Value
    for i in LED_value:
        GPIO.output(i,(temp%2))
        temp = temp//2
    


# Guess button
def btn_guess_pressed(channel):
    # If they've pressed and held the button, clear up the GPIO and take them back to the menu screen
    # Compare the actual value with the user value displayed on the LEDs
    # Change the PWM LED
    # if it's close enough, adjust the buzzer
    # if it's an exact guess:
    # - Disable LEDs and Buzzer
    # - tell the user and prompt them for a name
    start_t = time.time()
    global value, guess_Value,end_of_game,score
    while GPIO.input(channel) == 0:
        pass
    buttonTime = time.time() - start_t
    if buttonTime > 3 :
        AccuracyLED.ChangeDutyCycle(0)
        for i in LED_value:
            GPIO.output(i,(0))
        end_of_game = True
    else:
        if value == guess_Value:
            name = input("Guess is correct. \n Please enter you name(3 letters)")
            score +=1
            letters = len(name)
            print(letters)
            if(letters > 3):
                name = name[:3]
            elif (letters < 3):
                for a in range(3-letters):
                    name += "Z"
            print(name)
            AccuracyLED.ChangeDutyCycle(0)
            for i in LED_value:
                GPIO.output(i,(0))
            save_scores(name,score)
            end_of_game = True
        else:
            accuracy_leds()
            diff = abs(value - guess_Value)
            if diff < 4:
                trigger_buzzer(diff)
        
            
    # - fetch all the scores
    # - add the new score
    # - sort the scores
    # - Store the scores back to the EEPROM, being sure to update the score count
    


# LED Brightness
def accuracy_leds():
    # Set the brightness of the LED based on how close the guess is to the answer
    # - The % brightness should be directly proportional to the % "closeness"
    # - For example if the answer is 6 and a user guesses 4, the brightness should be at 4/6*100 = 66%
    # - If they guessed 7, the brightness would be at ((8-7)/(8-6)*100 = 50%
    global AccuracyLED,value,guess_Value
    print("AccLED")
    print(value)
    print(guess_Value)
    if guess_Value>value:
        AccuracyLED.ChangeDutyCycle((((8-guess_Value)/(8-value))*100))
    else:
        AccuracyLED.ChangeDutyCycle(((guess_Value/value)*100))

# Sound Buzzer
def trigger_buzzer(diff):
    # The buzzer operates differently from the LED
    # While we want the brightness of the LED to change(duty cycle), we want the frequency of the buzzer to change
    # The buzzer duty cycle should be left at 50%
    # If the user is off by an absolute value of 3, the buzzer should sound once every second
    # If the user is off by an absolute value of 2, the buzzer should sound twice every second
    # If the user is off by an absolute value of 1, the buzzer should sound 4 times a second
    print("Buzzer")

    global buzzerSetting
    buzzerSetting = diff
    


if __name__ == "__main__":
    try:
        # Call setup function
        setup()
        welcome()
        b = 1
        while True:
            print("Menu accessed count: {}".format(b))
            b += 1
            menu()
            pass
    except Exception as e:
        print(e)
    finally:
        GPIO.cleanup()
