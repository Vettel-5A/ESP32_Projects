from machine import SoftI2C
from machine import Pin
from time import sleep

class HT16K33:
    """
    A simple, generic driver for the I2C-connected Holtek HT16K33 controller chip.
    This release supports MicroPython and CircuitPython

    Bus:        I2C
    Author:     Tony Smith (@smittytone)
    License:    MIT
    Copyright:  2023
    """

    # *********** CONSTANTS **********

    HT16K33_GENERIC_DISPLAY_ON = 0x81
    HT16K33_GENERIC_DISPLAY_OFF = 0x80
    HT16K33_GENERIC_SYSTEM_ON = 0x21
    HT16K33_GENERIC_SYSTEM_OFF = 0x20
    HT16K33_GENERIC_DISPLAY_ADDRESS = 0x00
    HT16K33_GENERIC_CMD_BRIGHTNESS = 0xE0
    HT16K33_GENERIC_CMD_BLINK = 0x81

    # *********** PRIVATE PROPERTIES **********

    i2c = None
    address = 0
    brightness = 15
    flash_rate = 0

    # *********** CONSTRUCTOR **********

    def __init__(self, i2c, i2c_address):
        assert 0x00 <= i2c_address < 0x80, "ERROR - Invalid I2C address in HT16K33()"
        self.i2c = i2c
        self.address = i2c_address
        self.power_on()

    # *********** PUBLIC METHODS **********

    def set_blink_rate(self, rate=0):
        """
        Set the display's flash rate.

        Only four values (in Hz) are permitted: 0, 2, 1, and 0,5.

        Args:
            rate (int): The chosen flash rate. Default: 0Hz (no flash).
        """
        assert rate in (0, 0.5, 1, 2), "ERROR - Invalid blink rate set in set_blink_rate()"
        self.blink_rate = rate & 0x03
        self._write_cmd(self.HT16K33_GENERIC_CMD_BLINK | rate << 1)

    def set_brightness(self, brightness=15):
        """
        Set the display's brightness (ie. duty cycle).

        Brightness values range from 0 (dim, but not off) to 15 (max. brightness).

        Args:
            brightness (int): The chosen flash rate. Default: 15 (100%).
        """
        if brightness < 0 or brightness > 15: brightness = 15
        self.brightness = brightness
        self._write_cmd(self.HT16K33_GENERIC_CMD_BRIGHTNESS | brightness)

    def draw(self):
        """
        Writes the current display buffer to the display itself.

        Call this method after updating the buffer to update
        the LED itself.
        """
        self._render()

    def update(self):
        """
        Alternative for draw() for backwards compatibility
        """
        self._render()

    def clear(self):
        """
        Clear the buffer.

        Returns:
            The instance (self)
        """
        for i in range(0, len(self.buffer)): self.buffer[i] = 0x00
        return self

    def power_on(self):
        """
        Power on the controller and display.
        """
        self._write_cmd(self.HT16K33_GENERIC_SYSTEM_ON)
        self._write_cmd(self.HT16K33_GENERIC_DISPLAY_ON)

    def power_off(self):
        """
        Power on the controller and display.
        """
        self._write_cmd(self.HT16K33_GENERIC_DISPLAY_OFF)
        self._write_cmd(self.HT16K33_GENERIC_SYSTEM_OFF)

    # ********** PRIVATE METHODS **********

    def _render(self):
        """
        Write the display buffer out to I2C
        """
        buffer = bytearray(len(self.buffer) + 1)
        buffer[1:] = self.buffer
        buffer[0] = 0x00
        self.i2c.writeto(self.address, bytes(buffer))

    def _write_cmd(self, byte):
        """
        Writes a single command to the HT16K33. A private method.
        """
        self.i2c.writeto(self.address, bytes([byte]))


# Import the base class
#from ht16k33 import HT16K33

class HT16K33Segment(HT16K33):
    """
    Micro/Circuit Python class for the Adafruit 0.56-in 4-digit,
    7-segment LED matrix backpack and equivalent Featherwing.

    Bus:        I2C
    Author:     Tony Smith (@smittytone)
    License:    MIT
    Copyright:  2023
    """

    # *********** CONSTANTS **********

    HT16K33_SEGMENT_COLON_ROW = 0x04
    HT16K33_SEGMENT_MINUS_CHAR = 0x10
    HT16K33_SEGMENT_DEGREE_CHAR = 0x11
    HT16K33_SEGMENT_SPACE_CHAR = 0x12

    # The positions of the segments within the buffer
    POS = (0, 2, 6, 8)

    # Bytearray of the key alphanumeric characters we can show:
    # 0-9, A-F, minus, degree, space
    CHARSET = b'\x3F\x06\x5B\x4F\x66\x6D\x7D\x07\x7F\x6F\x5F\x7C\x58\x5E\x7B\x71\x40\x63\x00'

    # *********** CONSTRUCTOR **********

    def __init__(self, i2c, i2c_address=0x70):
        self.buffer = bytearray(16)
        self.is_rotated = False
        super(HT16K33Segment, self).__init__(i2c, i2c_address)

    # *********** PUBLIC METHODS **********

    def rotate(self):
        """
        Rotate/flip the segment display.

        Returns:
            The instance (self)
        """
        self.is_rotated = not self.is_rotated
        return self

    def set_colon(self, is_set=True):
        """
        Set or unset the display's central colon symbol.

        This method updates the display buffer, but does not send the buffer to the display itself.
        Call 'update()' to render the buffer on the display.

        Args:
            isSet (bool): Whether the colon is lit (True) or not (False). Default: True.

        Returns:
            The instance (self)
        """
        self.buffer[self.HT16K33_SEGMENT_COLON_ROW] = 0x02 if is_set is True else 0x00
        return self

    def set_glyph(self, glyph, digit=0, has_dot=False):
        """
        Present a user-defined character glyph at the specified digit.

        Glyph values are 8-bit integers representing a pattern of set LED segments.
        The value is calculated by setting the bit(s) representing the segment(s) you want illuminated.
        Bit-to-segment mapping runs clockwise from the top around the outside of the matrix; the inner segment is bit 6:

                0
                _
            5 |   | 1
              |   |
                - <----- 6
            4 |   | 2
              | _ |
                3

        This method updates the display buffer, but does not send the buffer to the display itself.
        Call 'update()' to render the buffer on the display.

        Args:
            glyph (int):   The glyph pattern.
            digit (int):   The digit to show the glyph. Default: 0 (leftmost digit).
            has_dot (bool): Whether the decimal point to the right of the digit should be lit. Default: False.

        Returns:
            The instance (self)
        """
        # Bail on incorrect row numbers or character values
        assert 0 <= digit < 4, "ERROR - Invalid digit (0-3) set in set_glyph()"
        assert 0 <= glyph < 0x80, "ERROR - Invalid glyph (0x00-0x80) set in set_glyph()"

        self.buffer[self.POS[digit]] = glyph
        if has_dot is True: self.buffer[self.POS[digit]] |= 0x80
        return self

    def set_number(self, number, digit=0, has_dot=False):
        """
        Present single decimal value (0-9) at the specified digit.

        This method updates the display buffer, but does not send the buffer to the display itself.
        Call 'update()' to render the buffer on the display.

        Args:
            number (int):  The number to show.
            digit (int):   The digit to show the number. Default: 0 (leftmost digit).
            has_dot (bool): Whether the decimal point to the right of the digit should be lit. Default: False.

        Returns:
            The instance (self)
        """
        # Bail on incorrect row numbers or character values
        assert 0 <= digit < 4, "ERROR - Invalid digit (0-3) set in set_number()"
        assert 0 <= number < 10, "ERROR - Invalid value (0-9) set in set_number()"

        return self.set_character(str(number), digit, has_dot)

    def set_character(self, char, digit=0, has_dot=False):
        """
        Present single alphanumeric character at the specified digit.

        Only characters from the class' character set are available:
        0, 1, 2, 3, 4, 5, 6, 7, 8, 9, a, b, c, d ,e, f, -.
        Other characters can be defined and presented using 'set_glyph()'.

        This method updates the display buffer, but does not send the buffer to the display itself.
        Call 'update()' to render the buffer on the display.

        Args:
            char (string):  The character to show.
            digit (int):    The digit to show the number. Default: 0 (leftmost digit).
            has_dot (bool): Whether the decimal point to the right of the digit should be lit. Default: False.

        Returns:
            The instance (self)
        """
        # Bail on incorrect row numbers
        assert 0 <= digit < 4, "ERROR - Invalid digit set in set_character()"

        char = char.lower()
        char_val = 0xFF
        if char == "deg":
            char_val = self.HT16K33_SEGMENT_DEGREE_CHAR
        elif char == '-':
            char_val = self.HT16K33_SEGMENT_MINUS_CHAR
        elif char == ' ':
            char_val = self.HT16K33_SEGMENT_SPACE_CHAR
        elif char in 'abcdef':
            char_val = ord(char) - 87
        elif char in '0123456789':
            char_val = ord(char) - 48

        # Bail on incorrect character values
        assert char_val != 0xFF, "ERROR - Invalid char string set in set_character()"

        self.buffer[self.POS[digit]] = self.CHARSET[char_val]
        if has_dot is True: self.buffer[self.POS[digit]] |= 0x80
        return self

    def draw(self):
        """
        Writes the current display buffer to the display itself.

        Call this method after updating the buffer to update
        the LED itself. Rotation handled here.
        """
        if self.is_rotated:
            # Swap digits 0,3 and 1,2
            a = self.buffer[self.POS[0]]
            self.buffer[self.POS[0]] = self.buffer[self.POS[3]]
            self.buffer[self.POS[3]] = a

            a = self.buffer[self.POS[1]]
            self.buffer[self.POS[1]] = self.buffer[self.POS[2]]
            self.buffer[self.POS[2]] = a

            # Rotate each digit
            for i in range(0, 4):
                a = self.buffer[self.POS[i]]
                b = (a & 0x07) << 3
                c = (a & 0x38) >> 3
                a &= 0xC0
                self.buffer[self.POS[i]] = (a | b | c)
        self._render()


# Import the base class
#from ht16k33 import HT16K33

class HT16K33Segment14(HT16K33):
    """
    Micro/Circuit Python class for the Adafruit 0.54in Quad Alphanumeric Display,
    a four-digit, 14-segment LED displays driven by the HT16K33 controller
    
    Bus:        I2C
    Author:     Tony Smith (@smittytone)
    License:    MIT
    Copyright:  2023
    """

    # *********** CONSTANTS **********

    HT16K33_SEG14_DP_VALUE      = 0x4000
    HT16K33_SEG14_BLANK_CHAR    = 62
    HT16K33_SEG14_DQUOTE_CHAR   = 64
    HT16K33_SEG14_QUESTN_CHAR   = 65
    HT16K33_SEG14_DOLLAR_CHAR   = 66
    HT16K33_SEG14_PRCENT_CHAR   = 67
    HT16K33_SEG14_DEGREE_CHAR   = 68
    HT16K33_SEG14_STAR_CHAR     = 72
    HT16K33_SEG14_PLUS_CHAR     = 73
    HT16K33_SEG14_MINUS_CHAR    = 74
    HT16K33_SEG14_DIVSN_CHAR    = 75
    HT16K33_SEG14_CHAR_COUNT    = 76

    VK16K33_SEG14_COLON_BYTE    = 1
    VK16K33_SEG14_DECIMAL_BYTE  = 3

    # CHARSET store character matrices for 0-9, A-Z, a-z, space and various symbols
    CHARSET = b'\x24\x3F\x00\x06\x00\xDB\x00\x8F\x00\xE6\x00\xED\x00\xFD\x00\x07\x00\xFF\x00\xEF\x00\xF7\x12\x8F\x00\x39\x12\x0F\x00\x79\x00\x71\x00\xBD\x00\xF6\x12\x09\x00\x1E\x0C\x70\x00\x38\x05\x36\x09\x36\x00\x3F\x00\xF3\x08\x3F\x08\xF3\x00\xED\x12\x01\x00\x3E\x24\x30\x28\x36\x2D\x00\x15\x00\x24\x09\x10\x58\x08\x78\x00\xD8\x20\x8E\x20\x58\x24\x80\x04\x8E\x10\x70\x10\x00\x08\x06\x1E\x00\x20\x30\x10\xD4\x10\x50\x00\xDC\x01\x70\x04\x86\x00\x50\x08\x88\x00\x78\x00\x1C\x08\x04\x28\x14\x2D\x00\x25\x00\x20\x48\x00\x00\x00\x06\x02\x20\x10\x83\x12\xED\x24\x24\x00\xE3\x04\x00\x09\x00\x20\x00\x3F\xC0\x12\xC0\x00\xC0\x24\x00'


    # *********** CONSTRUCTOR **********

    def __init__(self, i2c, i2c_address=0x70, is_ht16k33=False):
        self.buffer = bytearray(16)
        self.is_ht16k33 = is_ht16k33
        super(HT16K33Segment14, self).__init__(i2c, i2c_address)


    # *********** PUBLIC FUNCTIONS **********

    def set_glyph(self, glyph, digit=0, has_dot=False):
        """
        Puts the input character matrix (a 16-bit integer) into the specified row,
        adding a decimal point if required. Character matrix value is calculated by
        setting the bit(s) representing the segment(s) you want illuminated:

                0                9
                _
            5 |   | 1        8 \ | / 10
              |   |             \|/
                             6  - -  7
            4 |   | 2           /|\
              | _ |         13 / | \ 11    . 14
                3                12

        For HT16K33-based devices, swap bits 11 and 13: ie. set bit 13
        for a bottom right stroke, and bit 11 for a bottom left stroke.
        The diagram above is for the VK16K33. For the library's character
        set, this switch is done for you.

        Bit 14 is the period, but this is set with parameter 3.
        Bit 15 is not read by the display.

        Args:
            glyph (int):    The glyph pattern.
            digit (int):    The digit to show the glyph. Default: 0 (leftmost digit).
            has_dot (bool): Should the decimal point (where available) be illuminated?

        Returns:
            The instance (self)
        """
        # Bail on incorrect row numbers or character values
        assert 0 <= digit < 4, "ERROR - Invalid digit (0-3) set in set_glyph()"
        assert 0 <= glyph < 0xFFFF, "ERROR - Invalid glyph (0x0000-0xFFFF) set in set_glyph()"

        # Write the character to the buffer
        return self._set_digit(glyph, digit, has_dot)

    def set_number(self, number, digit=0, has_dot=False):
        """
        Present single decimal value (0-9) at the specified digit.

        This method updates the display buffer, but does not send the buffer to the display itself.
        Call 'update()' to render the buffer on the display.

        Args:
            number (int):   The number to show.
            digit (int):    The digit to show the number. Default: 0 (leftmost digit).
            has_dot (bool): Should the decimal point (where available) be illuminated?

        Returns:
            The instance (self)
        """
        # Bail on incorrect row numbers or character values
        assert 0 <= digit < 4, "ERROR - Invalid digit (0-3) set in set_number()"
        assert 0 <= number < 10, "ERROR - Invalid value (0-9) set in set_number()"

        # Write the character to the buffer
        return self.set_character(str(number), digit, has_dot)

    def set_character(self, char, digit=0, has_dot=False):
        """
        Present single alphanumeric character at the specified digit.

        Only characters from the class' character set are available:
        Other characters can be defined and presented using 'set_glyph()'.

        This method updates the display buffer, but does not send the buffer to the display itself.
        Call 'update()' to render the buffer on the display.

        Args:
            char (string):  The character to show.
            digit (int):    The digit to show the number. Default: 0 (leftmost digit).
            has_dot (bool): Should the decimal point (where available) be illuminated?

        Returns:
            The instance (self)
        """
        # Bail on incorrect row number
        assert 0 <= digit < 4, "ERROR - Invalid digit set in set_character()"

        # Determine the character's entry in the charset table
        char_val = 0xFFFF
        if char == '-':
            char_val = self.HT16K33_SEG14_MINUS_CHAR
        elif char == '*':
            char_val = self.HT16K33_SEG14_STAR_CHAR
        elif char == '+':
            char_val = self.HT16K33_SEG14_PLUS_CHAR
        elif char == ' ':
            char_val = self.HT16K33_SEG14_BLANK_CHAR
        elif char == '/':
            char_val = self.HT16K33_SEG14_DIVSN_CHAR
        elif char == '$':
            char_val = self.HT16K33_SEG14_DOLLAR_CHAR
        elif char == ':':
            char_val = self.HT16K33_SEG14_DQUOTE_CHAR
        elif char in '0123456789':
            char_val = ord(char) - 48   # 0-9
        elif char in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            char_val = ord(char) - 55   # 10-35
        elif char in 'abcdefghijklmnopqrstuvwxyz':
            char_val = ord(char) - 61   # 36-61

        # Bail on incorrect character values
        assert char_val != 0xFFFF, "ERROR - Invalid char string set in set_character() " + char + " (" + str(ord(char)) + ")"

        # Write the character to the buffer
        return self._set_digit((self.CHARSET[char_val << 1] << 8) | self.CHARSET[(char_val << 1) + 1], digit, has_dot)

    def set_code(self, code, digit, has_dot=False):
        """
        Present single alphanumeric character at the specified digit.

        Only characters from the class' character set are available:
        Other characters can be defined and presented using 'set_glyph()'.

        This method updates the display buffer, but does not send the buffer to the display itself.
        Call 'update()' to render the buffer on the display.

        Args:
            code (int):     The character's class-specific code.
            digit (int):    The digit to show the number. Default: 0 (leftmost digit).
            has_dot (bool): Should the decimal point (where available) be illuminated?

        Returns:
            The instance (self)
        """
        # Bail on incorrect row numbers or code values
        assert 0 <= digit < 4, "ERROR - Invalid digit (0-3) set in set_code()"
        assert 0 <= code < self.HT16K33_SEG14_CHAR_COUNT, "ERROR - Invalid code (0-{:d}) set in set_code()".format(self.HT16K33_SEG14_CHAR_COUNT - 1)

        # Write the character to the buffer
        return self._set_digit((self.CHARSET[code << 1] << 8) | self.CHARSET[(code << 1) + 1], digit, has_dot)

    def set_colon(self, is_on=True):
        """
        Set or unset the colon symbol on the SparkFun Alphamnumeric Display.

       Args:
            is_on (bool): Should the colon be illuminated?

        Returns:
            The instance (self)
        """
        # This doesn't work on the HT16K33
        if self.is_ht16k33: return self
        if is_on:
            self.buffer[self.VK16K33_SEG14_COLON_BYTE] |= 0x01
        else:
            self.buffer[self.VK16K33_SEG14_COLON_BYTE] &= 0xFE
        return self


    def set_decimal(self, is_on=True):
        """
        Set or unset the decimal point symbol on the SparkFun Alphamnumeric Display.

       Args:
            is_on (bool): Should the decimal point be illuminated?

        Returns:
            The instance (self)
        """
        # This doesn't work on the HT16K33
        if self.is_ht16k33: return self
        if is_on:
            self.buffer[self.VK16K33_SEG14_DECIMAL_BYTE] |= 0x01
        else:
            self.buffer[self.VK16K33_SEG14_DECIMAL_BYTE] &= 0x7F
        return self

    # *********** PRIVATE FUNCTIONS (DO NOT CALL) **********

    def _set_digit(self, value, digit, has_dot=False):

        if self.is_ht16k33:
            if has_dot: value |= self.HT16K33_SEG14_DP_VALUE
            # Output for HT16K33: swap bits 11 and 13,
            # and sequence becomes LSB, MSB
            msb = (value >> 8) & 0xFF
            b11 = msb & 0x08
            b13 = msb & 0x20
            msb &= 0xD7
            msb |= (b11 << 2)
            msb |= (b13 >> 2)
            self.buffer[(digit << 1) + 1] = msb
            self.buffer[digit << 1] = value & 0xFF
        else:
            # Output for VK16K33
            a = 0
            d = 1
            for i in range(0, 16):
                if (value & (1 << i)):
                    self.buffer[a] |= (d << digit)
                a += 2
                if i == 6:
                    a = 0
                    d = 16
        return self

#from ht16k33segment import HT16K33Segment
#from machine import I2C


# Update the pin values for your board
DEVICE_I2C_SCL_PIN = 20
DEVICE_I2C_SDA_PIN = 22


# Power On the I2C capabilities
powerpin2 = Pin(2, Pin.OUT)
powerpin2.value(1)

i2c = SoftI2C(scl=Pin(DEVICE_I2C_SCL_PIN), sda=Pin(DEVICE_I2C_SDA_PIN))
#devices = i2c.scan()
led = HT16K33Segment14(i2c)
#led.power_on()
#led.clear().draw()
naptime = 0.5
timer = 0.0
while timer < 100.0:
  sleep(0.1)
  timer += 0.1
  led.clear().draw()
  led.set_decimal().draw()
  if timer < 10.0:
    ones = str(timer)[0]
    tenths = str(timer)[2]
    led.set_character(ones, 2).set_character(tenths, 3)
  else:
    tens = str(timer)[0]
    ones = str(timer)[1]
    tenths = str(timer)[3]
    led.set_character(tens, 1).set_character(ones, 2).set_character(tenths, 3)
  led.draw()

