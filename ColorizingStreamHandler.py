﻿#!/usr/bin/env python
#encoding:utf-8

#
# Copyright (C) 2010, 2011 Vinay Sajip. All rights reserved.
#
#
# Modified by Chris Jensen 
# to add support for indentation of message based upon stack trace depth

import logging
import os
from Console import *

class ColorizingStreamHandler(logging.StreamHandler):
    # color names to indices
    color_map = {
        'black': 0,
        'red': 1,
        'green': 2,
        'yellow': 3,
        'blue': 4,
        'magenta': 5,
        'cyan': 6,
        'white': 7,
    }

    #levels to (background, foreground, bold/intense)
    level_map = {
        logging.DEBUG: (None, 'cyan', False),
        logging.INFO: (None, None, False),
        logging.WARNING: (None, 'green', False),
        logging.ERROR: (None, 'yellow', False),
        logging.CRITICAL: (None, 'red', False),
    }
    csi = '\x1b['
    reset = '\x1b[0m'

    @property
    def is_tty(self):
        isatty = getattr(self.stream, 'isatty', None)
        return isatty and isatty()

    def emit(self, record):
        try:
            message = self.format(record)
            stream = self.stream
            if not self.is_tty:
                stream.write(message)
            else:
                self.output_colorized(message)
            stream.write(getattr(self, 'terminator', '\n'))
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

    if os.name != 'nt':
        def output_colorized(self, message):
            self.stream.write(message.encode('utf-8'))
    else:
        try:
            import ctypes
            #call this here to cause an exception to be thrown if ctypes doesn't exist
            ctypes.windll.kernel32.GetStdHandle(-10)
            import re
            ansi_esc = re.compile(r'\x1b\[((?:\d+)(?:;(?:\d+))*)m')
            
            nt_color_map = {
                0: 0x00,    # black
                1: 0x04,    # red
                2: 0x02,    # green
                3: 0x06,    # yellow
                4: 0x01,    # blue
                5: 0x05,    # magenta
                6: 0x03,    # cyan
                7: 0x07,    # white
            }
            
            def output_colorized(self, message):
                import ctypes
                parts = self.ansi_esc.split(message)
                write = self.stream.write
                h = None
                fd = getattr(self.stream, 'fileno', None)
                if fd is not None:
                    fd = fd()
                    if fd in (1, 2): # stdout or stderr
                        h = ctypes.windll.kernel32.GetStdHandle(-10 - fd)
                while parts:
                    text = parts.pop(0)
                    if text:
                        write(text)
                    if parts:
                        params = parts.pop(0)
                        if h is not None:
                            params = [int(p) for p in params.split(';')]
                            color = 0
                            for p in params:
                                if 40 <= p <= 47:
                                    color |= self.nt_color_map[p - 40] << 4
                                elif 30 <= p <= 37:
                                   color |= self.nt_color_map[p - 30]
                                elif p == 1:
                                    color |= 0x08 # foreground intensity on
                                elif p == 0: # reset to default color
                                    color = 0x07
                                else:
                                    pass # error condition ignored
                            ctypes.windll.kernel32.SetConsoleTextAttribute(h, color)            
        except:
            def output_colorized(self, message):
                message = message.replace('\x1b[31m', '')
                message = message.replace('\x1b[32m', '')
                message = message.replace('\x1b[33m', '')
                message = message.replace('\x1b[36m', '')
                message = message.replace('\x1b[0m', '')
                self.stream.write('test'+message.encode('utf-8'))

    def colorize(self, message, record):
        if record.levelno in self.level_map:
            bg, fg, bold = self.level_map[record.levelno]
            params = []
            if bg in self.color_map:
                params.append(str(self.color_map[bg] + 40))
            if fg in self.color_map:
                params.append(str(self.color_map[fg] + 30))
            if bold:
                params.append('1')
            if params:
                message = ''.join((self.csi, ';'.join(params),
                                   'm', message, self.reset))
        return message
    
    def format(self, record):
        message = logging.StreamHandler.format(self, record)
        if self.is_tty:
            # Don't colorize any traceback
            parts = message.split('\n', 1)
            parts[0] = self.colorize(parts[0], record)
            message = '\n'.join(parts)
        return indent_text(message)
