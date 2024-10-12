#encoding: utf-8
from __future__ import division
from nodebox.graphics import *
import pymunk
import pymunk.pyglet_util
import random
import math
import numpy as np

space = pymunk.Space()

def createBody(x, y, shape, *shapeArgs):
    body = pymunk.Body()
    body.position = x, y
    s = shape(body, *shapeArgs)
    s.mass = 1
    s.friction = 0.5  # Зменшено тертя для більш реалістичних рухів
    space.add(body, s)
    return s  # shape!!!

s0 = createBody(300, 300, pymunk.Poly, ((-20, -5), (-20, 5), (20, 15), (20, -15)))
s0.color = (0, 0, 255, 255)  # Синій
s0.score = 0

s3 = createBody(200, 300, pymunk.Poly, ((-20, -5), (-20, 5), (20, 15), (20, -15)))
s3.color = (0, 255, 0, 255)
s3.score = 0
s3.body.Q = [[0, 0], [0, 0], [0, 0]]
s3.body.action = 0  # 0 - залишати, 1 - змінювати

s1 = createBody(300, 200, pymunk.Circle, 10, (0, 0))
S2 = []
for i in range(1):
    s2 = createBody(350, 250, pymunk.Circle, 10, (0, 0))
    s2.color = (255, 0, 0, 255)
    S2.append(s2)

# Параметри для епсилон-жадібної політики
epsilon = 1.0  # Початкове значення
epsilon_decay = 0.995  # Швидкість зменшення
epsilon_min = 0.1  # Мінімальне значення

# Параметри для Q-навчання
alpha = 0.1  # Швидкість навчання
gamma = 0.9  # Дисконтна ставка

def getAngle(x, y, x1, y1):
    return math.atan2(y1 - y, x1 - x)

def getDist(x, y, x1, y1):
    return ((x - x1) ** 2 + (y - y1) ** 2) ** 0.5

def inCircle(x, y, cx, cy, R):
    return (x - cx) ** 2 + (y - cy) ** 2 < R ** 2

def inSector(x, y, cx, cy, R, a):
    angle = getAngle(cx, cy, x, y)
    a = a % (2 * math.pi)
    angle = angle % (2 * math.pi)
    return inCircle(x, y, cx, cy, R) and (a - 0.5 < angle < a + 0.5)

def getState(b):
    """Визначає стан агента на основі положення об'єктів."""
    inS = inSector(s1.body.position[0], s1.body.position[1], b.position[0], b.position[1], 100, b.angle)
    inS2 = inSector(S2[0].body.position[0], S2[0].body.position[1], b.position[0], b.position[1], 100, b.angle)

    if inS:
        return 1  # Об'єкт
    elif inS2:
        return 2  # Антиоб'єкт
    else:
        return 0  # Нічого

def strategy2(b=s3.body):
    v = 100
    a = b.angle
    b.velocity = v * cos(a), v * sin(a)
    x, y = b.position
    R = getDist(x, y, 350, 250)
    ellipse(x, y, 200, 200, stroke=Color(0))

    # Відображення сектора
    sector_angle_range = 0.5  # Кутовий радіус сектора
    line(x, y, x + 100 * cos(a - sector_angle_range), y + 100 * sin(a - sector_angle_range), stroke=Color(0.5))
    line(x, y, x + 100 * cos(a + sector_angle_range), y + 100 * sin(a + sector_angle_range), stroke=Color(0.5))

    if canvas.frame % 10 == 0:  # кожні n кадрів
        state = getState(b)
        
        # Нагорода
        reward = 0
        if inSector(s1.body.position[0], s1.body.position[1], x, y, 100, a):
            reward += 1  # Позитивна нагорода за об'єкт
        elif inSector(S2[0].body.position[0], S2[0].body.position[1], x, y, 100, a):
            reward -= 1  # Негативна нагорода за антиоб'єкт

        # Оновлення Q-таблиці
        next_state = getState(b)
        b.Q[state][b.action] += alpha * (reward + gamma * np.max(b.Q[next_state]) - b.Q[state][b.action])

        # Вибір дії
        if random.random() < epsilon:
            b.action = random.choice([0, 1])  # Випадкова дія
        else:
            b.action = np.argmax(b.Q[state])  # Оптимальна дія

        if b.action:  # якщо змінювати
            b.angle = 2 * math.pi * random.random()

        # Зменшення епсілона
        global epsilon
        epsilon = max(epsilon_min, epsilon * epsilon_decay)

        if R > 180:  # запобігти виїзду за межі
            b.angle = getAngle(x, y, 350, 250)

def scr(s, s0, s3, p=1):
    bx, by = s.body.position
    s0x, s0y = s0.body.position
    s3x, s3y = s3.body.position
    if not inCircle(bx, by, 350, 250, 180):
        if getDist(bx, by, s0x, s0y) < getDist(bx, by, s3x, s3y):
            s0.score += p
        else:
            s3.score += p
        s.body.position = random.randint(200, 400), random.randint(200, 300)

def score():
    scr(s1, s0, s3)
    for s in S2:
        scr(s, s0, s3, p=-1)

def manualControl():
    v = 10  # швидкість
    b = s0.body
    a = b.angle
    x, y = b.position
    if canvas.keys.char == "a":
        b.angle -= 0.1
    if canvas.keys.char == "d":
        b.angle += 0.1
    if canvas.keys.char == "w":
        b.velocity = (b.velocity[0] + v * cos(a), b.velocity[1] + v * sin(a))
    if canvas.mouse.button == LEFT:
        b.angle = getAngle(x, y, *canvas.mouse.xy)
        b.velocity = (b.velocity[0] + v * cos(b.angle), b.velocity[1] + v * sin(b.angle))

def simFriction():
    for s in [s0, s1, s3] + S2:
        s.body.velocity = s.body.velocity[0] * 0.9, s.body.velocity[1] * 0.9
        s.body.angular_velocity = s.body.angular_velocity * 0.9

draw_options = pymunk.pyglet_util.DrawOptions()

def draw(canvas):
    canvas.clear()
    fill(0, 0, 0, 1)
    text("%i %i" % (s0.score, s3.score), 20, 20)
    nofill()
    ellipse(350, 250, 350, 350, stroke=Color(0))
    manualControl()
    strategy2()
    score()
    simFriction()
    space.step(0.02)
    space.debug_draw(draw_options)

canvas.size = 700, 500
canvas.run(draw)
