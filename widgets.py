import pygame as pg
from settings import *


class EntryBox:
    def __init__(self, x, y, width, font, valid_chars, text=""):
        font = pg.font.Font(font, ENTRY_SIZE)
        self.font = font
        self.text = text
        self.fillcolor = ENTRY_INACTIVE_COLOR
        self.active = False
        self.valid_chars = valid_chars
        # render text
        self.text_surface = self.font.render(self.text, True, TEXT_COLOR)
        self.rect = pg.Rect(x, y, width, self.text_surface.get_height())

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

        # add or delete a character from the entry box
        if event.type == pg.KEYDOWN:
            if self.active:
                if event.key == pg.K_RETURN:
                    self.active = False
                elif event.key == pg.K_BACKSPACE:
                    self.text = self.text[:-1]
                elif event.unicode in self.valid_chars:
                    self.text += event.unicode
                self.text_surface = self.font.render(self.text, True, TEXT_COLOR)
                # delete the character just entered if it would go off the entry box
                if self.text_surface.get_width() > ENTRY_WIDTH - ENTRY_TEXT_OFFSET * 2:
                    self.text = self.text[:-1]
                    self.text_surface = self.font.render(self.text, True, TEXT_COLOR)

    def draw(self, surface):
        # entry box fill
        pg.draw.rect(surface, self.fillcolor, self.rect)
        # blit the text with a slight offset to center it
        surface.blit(self.text_surface, (self.rect.x + ENTRY_TEXT_OFFSET, self.rect.y))
        # entry box boundary
        pg.draw.rect(surface, DARK_GRAY, self.rect, 2)


class Button:
    def __init__(self, x, y, width, height, font, text=""):
        self.rect = pg.Rect(x, y, width, height)
        self.fillcolor = BUTTON_INACTIVE
        self.active = False
        self.pressed = False
        font = pg.font.Font(font, BUTTON_SIZE)
        # render text
        self.text_surface = font.render(text, True, TEXT_COLOR)

    def events(self, event, mouse_pos):
        # if the button should execute some code or not
        execute = False

        # test for the current status of the button
        if self.rect.collidepoint(mouse_pos):
            self.active = True

            if event.type == pg.MOUSEBUTTONDOWN:
                self.pressed = True
        else:
            self.active = False

        if event.type == pg.MOUSEBUTTONUP and self.pressed:
            if self.rect.collidepoint(event.pos):
                execute = True
                self.pressed = False
            else:
                self.pressed = False

        # update color
        if self.active:
            self.fillcolor = BUTTON_ACTIVE
        if self.pressed:
            self.fillcolor = BUTTON_PRESSED
        if not self.active and not self.pressed:
            self.fillcolor = BUTTON_INACTIVE

        return execute

    def draw(self, surface):
        # button fill
        pg.draw.rect(surface, self.fillcolor, self.rect)
        # blit the text with a slight offset to center it
        surface.blit(self.text_surface, (self.rect.x + self.rect.width / 2 - self.text_surface.get_width() / 2,
                                         self.rect.y + self.rect.height / 2 - self.text_surface.get_height() / 2))
        # button boundary
        pg.draw.rect(surface, DARK_GRAY, self.rect, 2)
