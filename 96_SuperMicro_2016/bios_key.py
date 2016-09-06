#!/usr/bin/env python

import time
from pykeyboard import PyKeyboard

time.sleep(2)

k = PyKeyboard()

def slow_tap(k, character, n=1, interval=0.25):
    for _ in range(n):
        k.press_key(character)
        time.sleep(.25)
        k.release_key(character)
        time.sleep(interval)

# Move from main to Advanced tab
slow_tap(k, k.right_key)

# Enter SATA menu
slow_tap(k, k.down_key, n=3)
slow_tap(k, k.enter_key)

# Move to Configure SATA as
slow_tap(k, k.down_key)

# Set to Legacy

slow_tap(k, '-')

slow_tap(k, k.escape_key)

# To PCI Configuration
slow_tap(k, k.down_key, n=3)
slow_tap(k, k.enter_key)

# To LAN OPROM
slow_tap(k, k.down_key, n=10)
slow_tap(k, '-')

# To NVME
slow_tap(k, k.down_key, n=3)

for _ in range(3):
    slow_tap(k, '-')
    slow_tap(k, k.down_key)

slow_tap(k, k.escape_key)

# To BOOT Menu
slow_tap(k, k.right_key, n=4)

# Boot -> Legacy
slow_tap(k, k.down_key)
slow_tap(k, '-')

# Netboot
slow_tap(k, k.down_key)
slow_tap(k, '+', n=2)

# Save and exit
slow_tap(k, k.right_key)
slow_tap(k, k.down_key)
slow_tap(k, k.enter_key)
