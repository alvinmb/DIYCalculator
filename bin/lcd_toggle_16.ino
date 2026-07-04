/*
  16x2 LCD Toggle Display
  -----------------------
  When the toggle switch is OFF, the LCD looks "off":
    - backlight is dark
    - screen is cleared (no characters showing)
  When the toggle switch is ON, the LCD wakes up and shows:
    - backlight on
    - "16 -" written in the LCD's normal black pixels

  Wiring (standard parallel HD44780 in 4-bit mode):
    LCD RS  -> Arduino pin 12
    LCD EN  -> Arduino pin 11
    LCD D4  -> Arduino pin  5
    LCD D5  -> Arduino pin  4
    LCD D6  -> Arduino pin  3
    LCD D7  -> Arduino pin  2
    LCD VSS -> GND
    LCD VDD -> 5V
    LCD V0  -> contrast pot wiper (10k pot between 5V and GND)
    LCD RW  -> GND

  Backlight:
    LCD A   -> Arduino pin 10 (through 220R resistor; or through a
                                transistor for higher current modules)
    LCD K   -> GND

  Toggle switch (latching SPST):
    one leg -> Arduino pin 7
    other   -> GND
    (we use the internal pull-up, so closed switch = LOW = ON)
*/

#include <LiquidCrystal.h>

// LCD pins: RS, EN, D4, D5, D6, D7
LiquidCrystal lcd(12, 11, 5, 4, 3, 2);

const uint8_t SWITCH_PIN    = 7;
const uint8_t BACKLIGHT_PIN = 10;

int lastSwitchState = -1;   // force an update on first loop

void showOff() {
  lcd.clear();                       // wipe any characters
  lcd.noDisplay();                   // controller stops driving pixels
  digitalWrite(BACKLIGHT_PIN, LOW);  // backlight off -> panel looks dark
}

void showOn() {
  digitalWrite(BACKLIGHT_PIN, HIGH); // light it up
  lcd.display();                     // re-enable pixel output
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("16 -");                 // black characters on lit panel
}

void setup() {
  pinMode(SWITCH_PIN, INPUT_PULLUP);
  pinMode(BACKLIGHT_PIN, OUTPUT);

  lcd.begin(16, 2);
  showOff();                         // boot in the "off" appearance
}

void loop() {
  // INPUT_PULLUP: LOW when switch is closed (ON), HIGH when open (OFF)
  int switchState = (digitalRead(SWITCH_PIN) == LOW) ? 1 : 0;

  if (switchState != lastSwitchState) {
    if (switchState == 1) {
      showOn();
    } else {
      showOff();
    }
    lastSwitchState = switchState;
    delay(50);  // small debounce
  }
}
