import pygame as pg
from settings import *


class EntryBox():
    def __init__(self, x, y, width, height, font, text=''):
        self.rect = pg.Rect(x, y, width, height)
        font = pg.font.Font(font, ENTRY_SIZE)
        self.font = font
        self.text = text
        self.fillcolor = ENTRY_INACTIVE_COLOR
        self.active = False
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
                    self.text = self.text[:-1]
                elif event.unicode in VALID_CHARS and len(self.text) < MAX_ENTRY_LENGTH:
                    self.text += event.unicode
                self.text_surface = self.font.render(self.text, True, TEXT_COLOR)

    def draw(self, surface):
        # blit the text with a slight offset to center it
        surface.blit(self.text_surface, (self.rect.x + 5, self.rect.y + 5))
        # entry box boundary
        pg.draw.rect(surface, self.fillcolor, self.rect, 2)
