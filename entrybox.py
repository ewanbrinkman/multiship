import pygame as pg
from settings import *


class EntryBox():
    def __init__(self, x, y, width, height, font, valid_chars, text=''):
        self.rect = pg.Rect(x, y, width, height)
        font = pg.font.Font(font, ENTRY_SIZE)
        self.font = font
        self.default_text = text
        self.text = text
        self.fillcolor = ENTRY_INACTIVE_COLOR
        self.active = False
        self.valid_chars = valid_chars
        # render text
        self.text_surface = self.font.render(self.text, True, TEXT_COLOR)

    def events(self, event):
        # if the user clicks on the entry box
        if event.type == pg.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                # toggle if active or not
                self.active = not self.active
            else:
                # user clicked somewhere else, entry box no longer active
                self.active = False
            # update color
            if self.active:
                self.fillcolor = ENTRY_ACTIVE_COLOR
            else:
                self.fillcolor = ENTRY_INACTIVE_COLOR
        if event.type == pg.KEYDOWN:
            if self.active:
                if event.key == pg.K_RETURN:
                    self.active = False
                elif event.key == pg.K_BACKSPACE:
                    # delete the whole entry, which would say something like "enter username"
                    if self.text == self.default_text:
                        self.text = ''
                        self.default_text = None
                    # delete the last character
                    else:
                        self.text = self.text[:-1]
                elif event.unicode in self.valid_chars and len(self.text) < MAX_ENTRY_LENGTH:
                    # delete the whole entry, which would say something like "enter username"
                    if self.text == self.default_text:
                        self.text = ''
                        self.default_text = None
                    self.text += event.unicode
                self.text_surface = self.font.render(self.text, True, TEXT_COLOR)

    def draw(self, surface):
        # blit the text with a slight offset to center it
        surface.blit(self.text_surface, (self.rect.x + 5, self.rect.y + 5))
        # entry box boundary
        pg.draw.rect(surface, self.fillcolor, self.rect, 2)
