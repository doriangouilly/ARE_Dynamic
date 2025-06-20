import pygame
from pygame.locals import *

class Config:
    def __init__(self, slider_rect):
        self.active = True
        self.params = {
            'n_hab': 1500,
            'n_ent': 75,
            'dist_importance': 1.0,
            'smic': 1461
        }
        self.panel_w, self.panel_h = 750, 160  
        self.x_pos = slider_rect.x 
        self.y_pos = slider_rect.bottom + 10
        self.simulation_started = False
        self.request_start = False
        self.request_stop = False
        self.create_elements()

    def create_elements(self):
        self.font = pygame.font.SysFont("Trebuchet MS", 21)
        self.font_bouton = pygame.font.SysFont("Trebuchet MS", 28)
        self.labels = []
        self.inputs = {}
        textes = [
            "Nombre d'habitant(s) :",
            "Nombre d'entreprise(s) :",
            "Coefficient distance :",
            "SMIC (€) :"
        ]
        keys = ['n_hab', 'n_ent', 'dist_importance', 'smic']
        oy = 10
        #COLONNE DE GAUCHE
        for key, txt in zip(keys[:2], textes[:2]):
            lbl_rect = pygame.Rect(10, oy, 250, 30)
            inp_rect = pygame.Rect(260, oy, 100, 25)
            self.labels.append({'text': txt, 'rect': lbl_rect})
            self.inputs[key] = {
                'rect': inp_rect,
                'value': str(self.params[key]),
                'active': False
            }
            oy += 40

        oy = 10
        #COLONNE DE DROITE
        for key, txt in zip(keys[2:], textes[2:]):
            lbl_rect = pygame.Rect(self.panel_w//2 + 10, oy, 250, 30)
            inp_rect = pygame.Rect(self.panel_w//2 + 260, oy, 100, 25)
            self.labels.append({'text': txt, 'rect': lbl_rect})
            self.inputs[key] = {
                'rect': inp_rect,
                'value': str(self.params[key]),
                'active': False
            }
            oy += 40

        self.start_btn = pygame.Rect(
            (self.panel_w - 200) // 2,
            oy + 20,
            200,
            40
        )

    def draw(self, surface):
        overlay = pygame.Surface((self.panel_w, self.panel_h), pygame.SRCALPHA)
        overlay.fill((30, 30, 30, 200))
        pygame.draw.rect(overlay, (255,255,255), (0,0,self.panel_w,self.panel_h), 2)
        surface.blit(overlay, (self.x_pos, self.y_pos))

        for label in self.labels:
            surf = self.font.render(label['text'], True, (255,255,255))
            surface.blit(surf, (self.x_pos + label['rect'].x, self.y_pos + label['rect'].y))

        for key, inp in self.inputs.items():
            color = (150,150,150) if self.simulation_started else (255,255,255) if inp['active'] else (150,150,150)
            pygame.draw.rect(surface, color, (self.x_pos + inp['rect'].x, self.y_pos + inp['rect'].y, inp['rect'].w, inp['rect'].h), 2)
            txt = self.font.render(inp['value'], True, (255,255,255))
            surface.blit(txt, (self.x_pos + inp['rect'].x +5, self.y_pos + inp['rect'].y +3))

        btn_color = (180, 0, 0) if self.simulation_started else (0, 180, 0)
        btn_text = "STOP" if self.simulation_started else "DÉMARRER"
        pygame.draw.rect(surface, btn_color, (self.x_pos + self.start_btn.x, self.y_pos + self.start_btn.y, self.start_btn.w, self.start_btn.h))
        txt = self.font_bouton.render(btn_text, True, (255,255,255))
        surface.blit(txt, (self.x_pos + self.start_btn.x + 20, self.y_pos + self.start_btn.y + 8))

    def handle_event(self, event):
        if event.type == MOUSEBUTTONDOWN:
            btn_click_x = event.pos[0] - self.x_pos
            btn_click_y = event.pos[1] - self.y_pos
            if self.start_btn.collidepoint(btn_click_x, btn_click_y):
                if self.simulation_started:
                    self.request_stop = True
                    self.simulation_started = False
                else:
                    self.validate_inputs()
                    self.request_start = True
                    self.simulation_started = True
                return 
            if not self.simulation_started:
                for key, inp in self.inputs.items():
                    inp['active'] = (self.x_pos + inp['rect'].x <= event.pos[0] <= self.x_pos + inp['rect'].x + inp['rect'].w and
                                     self.y_pos + inp['rect'].y <= event.pos[1] <= self.y_pos + inp['rect'].y + inp['rect'].h)
        elif event.type == KEYDOWN and not self.simulation_started:
            for key, inp in self.inputs.items():
                if not inp['active']:
                    continue
                if event.key == K_RETURN:
                    inp['active'] = False
                elif event.key == K_BACKSPACE:
                    inp['value'] = inp['value'][:-1]
                else:
                    if (key == 'dist_importance' and event.unicode in '0123456789.') or event.unicode.isdigit():
                        inp['value'] += event.unicode

    def validate_inputs(self):
        try:
            self.params['n_hab'] = int(self.inputs['n_hab']['value'])
            self.params['n_ent'] = int(self.inputs['n_ent']['value'])
            self.params['dist_importance'] = float(self.inputs['dist_importance']['value'])
            self.params['smic'] = int(self.inputs['smic']['value'])
        except ValueError:
            self.params = {'n_hab': 1500, 'n_ent': 75, 'dist_importance': 1.0, 'smic': 1461}