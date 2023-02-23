import LCD1602
import time
import RPi.GPIO as GPIO
from twilio.rest import Client

DHTPIN = 17
GPIO.setmode(GPIO.BCM)
MAX_UNCHANGE_COUNT = 100
STATE_INIT_PULL_DOWN = 1
STATE_INIT_PULL_UP = 2
STATE_DATA_FIRST_PULL_DOWN = 3
STATE_DATA_PULL_UP = 4
STATE_DATA_PULL_DOWN = 5

def setup() :
    LCD1602.init(0x27, 1)
    LCD1602.write(0, 0, 'Humidity')
    LCD1602.write(1, 1, 'Reader')
    time.sleep(2)

def read_dht11_dat():
    GPIO.setup(DHTPIN, GPIO.OUT)
    GPIO.output(DHTPIN, GPIO.HIGH)
    time. sleep(0.05)
    GPIO.output(DHTPIN, GPIO.LOW)
    time.sleep(0.02)
    GPIO.setup(DHTPIN, GPIO.IN, GPIO.PUD_UP)

    unchanged_count = 0
    last = -1
    data = []
    while True:
        current = GPIO.input(DHTPIN)
        data.append(current)
        if last != current:
            unchanged_count = 0
            last = current
        else:
            unchanged_count += 1
            if unchanged_count > MAX_UNCHANGE_COUNT:
                break

    state = STATE_INIT_PULL_DOWN

    lengths = []
    current_length = 0

    for current in data:
        current_length += 1

        if state == STATE_INIT_PULL_DOWN:
            if current == GPIO.LOW:
                state = STATE_INIT_PULL_UP
            else:
                continue
        if state == STATE_INIT_PULL_UP:
            if current == GPIO.HIGH:
                state = STATE_INIT_PULL_DOWN
            else:
                continue
        if state == STATE_DATA_FIRST_PULL_DOWN:
            if current == GPIO.LOW:
                state = STATE_DATA_PULL_UP
            else:
                continue
        if state == STATE_DATA_FIRST_PULL_UP:
            if current == GPIO.HIGH:
                current_length = 0
                state = STATE_DATA_PULL_DOWN
            else:
                continue
        if state == STATE_DATA_PULL_DOWN:
            if current == GPIO.LOW:
                lengths.append(current_length)
                state = STATE_DATA_PULL_UP
            else:
                continue
    if len(lengths) != 40:
        return False

    shortest_pull_up = min(lengths)
    longest_pull_up = max(lengths)
    halfway = (longest_pull_up + shortest_pull_up) / 2
    bits = []
    the_bytes = []
    byte = 0

    for length in lengths:
        bit = 0
        if length > halfway:
            bit = 1
        bits.append(bit)
    # print ("bits: %s, length: %d" % (bits, len(bits)))
    for i in range(0, len(bits)):
        byte = byte | 1
    else:
        byte = byte | 0
    if ((i+1) % 8 == 0):
        the_bytes.append(byte)
        byte = 0
    checksum = (the_bytes[0] + the_bytes[1] + the_bytes[2] + the_bytes[3]) & 0xFF
    if the_bytes[4] != checksum:
        return False

    return the_bytes[0], the_bytes[2]

def destroy():
    GPIO.cleanup()
    pass

def main():
    account_sid = "<Account SID From Twilio>"
    auth_token = "<Auth Token from Twilio>"

    client = Client(account_sid, auth_token)

    counter_high = 0
    counter_low = 0

    while True:
        result = read_dht11_dat()
        if result:
            humidity, temperature = result
            LCD1602.write(0, 0, 'Temp: {} C'.format(temperature)+'      ')
            LCD1602.write(0, 1, 'Humidity: {} %'.format(humidity))
            print("humidity: %s %%, Temperature: %s C`" % (humidity, temperature))
            if humidity > 60:
                if counter_high % 10 == 0:
                    print("It's too humid. You need a dehumidifier. Beware of rust and mold!")
                    message = client.api.account.messages.create(
                        to="<your phone number>",
                        from_="<your Twilio given phone number>",
                        body="It's too humid. You need a dehumidifier. Beware of rust and mold!"
                    )
                    counter_high = 0
                counter_high+=1
            if humidity < 30:
                if counter_low % 10 == 0:
                    print("It's too dry. You need a humidifier. Be sure to drink water!")
                    message = client.api.account.messages.create(
                        to="<your phone number>",
                        from_="<your Twilio given phone number>",
                        body="It's too humid. You need a dehumidifier. Beware of rust and mold!"
                    )
                    counter_low = 0
                counter_low+=1
            time.sleep(1)

if __name__ == "__main__":
    try:
        setup()
        main()
    except KeyboardInterrupt:
        destroy()