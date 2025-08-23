import usb.core
import usb.util


class PixelRing:
    """Controller for ReSpeaker LED ring interface.
    
    Provides methods to control the LED ring patterns for visual feedback
    during voice interaction states (listening, speaking, thinking, etc).
    """
    TIMEOUT = 8000

    def __init__(self, dev = None):
        try:
            if dev:
                self.dev = dev
            else:
                dev = usb.core.find(idVendor=0x2886, idProduct=0x0018)
                if not dev:
                    print('PixelRing not found')
                    exit(1)
                self.dev = dev
        except usb.core.USBError as e:
            print(f"USBError: {str(e)}")
            exit(1)
        except Exception as e:
            print(f"Error: {str(e)}")
            exit(1)
    

    def trace(self):
        self.write(0)

    def mono(self, color):
        self.write(1, [(color >> 16) & 0xFF, (color >> 8) & 0xFF, color & 0xFF, 0])
    
    def set_color(self, rgb=None, r=0, g=0, b=0):
        if rgb:
            self.mono(rgb)
        else:
            self.write(1, [r, g, b, 0])

    def off(self):
        self.mono(0)

    def listen(self, direction=None):
        self.write(2)

    wakeup = listen

    def speak(self):
        self.write(3)

    def think(self):
        self.write(4)

    wait = think

    def spin(self):
        self.write(5)

    def show(self, data):
        self.write(6, data)

    customize = show
        
    def set_brightness(self, brightness):
        self.write(0x20, [brightness])
    
    def set_color_palette(self, a, b):
        self.write(0x21, [(a >> 16) & 0xFF, (a >> 8) & 0xFF, a & 0xFF, 0, (b >> 16) & 0xFF, (b >> 8) & 0xFF, b & 0xFF, 0])

    def set_vad_led(self, state):
        self.write(0x22, [state])

    def set_volume(self, volume):
        self.write(0x23, [volume])

    def change_pattern(self, pattern=None):
        print('Not support to change pattern')

    def write(self, cmd, data=[0]):
        self.dev.ctrl_transfer(
            usb.util.CTRL_OUT | usb.util.CTRL_TYPE_VENDOR | usb.util.CTRL_RECIPIENT_DEVICE,
            0, cmd, 0x1C, data, self.TIMEOUT)

    def close(self):
        """
        close the interface
        """
        pixel_ring.off()
        usb.util.dispose_resources(self.dev)




if __name__ == '__main__':
    import time

    pixel_ring = PixelRing()

    while True:
        try:
            pixel_ring.wakeup(180)
            print("wakeup(180) mode")
            time.sleep(10)

            pixel_ring.listen()
            print("listen(command 2) mode")
            time.sleep(10)

            pixel_ring.speak()
            print("speak(command 3) mode")
            time.sleep(10)

            pixel_ring.think()
            print("think(command 4) mode")
            time.sleep(10)

            pixel_ring.spin()
            print("spin(command 5) mode")
            time.sleep(10)

            pixel_ring.set_volume(8)
            print("set volume to 8")
            time.sleep(3)

            pixel_ring.off()
            print("off mode")
            time.sleep(10)

        except KeyboardInterrupt:
            pixel_ring.close()
            break
