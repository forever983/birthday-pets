#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Valorant Desktop Pets - NO Context Menu Version"""

import os
import sys
import random
import math

from PyQt5.QtWidgets import QApplication, QLabel, QWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QPainter, QImage, QTransform, QCursor

try:
    from PIL import Image
    HAS_PIL = True
except:
    HAS_PIL = False

# ============================================================
# 火车模式全局变量
# ============================================================
train_mode = False
train_leader = None
train_order = []
TRAIN_PHRASES = ["乐乐", "卡了", "黑色的弩箭", "主人赠予的19岁火车出发咯！"]

# ============================================================
# 回城模式全局变量
# ============================================================
recall_mode = False
recall_finished = False  # 回城动画是否已完成
recall_order = []
recall_dest_x = 0
recall_dest_y = 0
recall_head_index = 0
recall_fading_pet = None
recall_fade_timer = 0

# ============================================================
# 击鼓传康模式全局变量
# ============================================================
potato_mode = False
potato_finished = False
potato_order = []
potato_circle_cx = 0  # 圆圈中心 X
potato_circle_cy = 0  # 圆圈中心 Y
potato_circle_r = 0  # 圆圈半径
potato_highlight_idx = 0
potato_rotate_timer = 0
potato_rotate_interval = 3  # 当前轮转间隔（ticks）
potato_phase = 0  # 0=聚拢, 1=旋转, 2=结束
potato_phase_timer = 0
potato_rotation_count = 0

# ============================================================
# 生日祝福大合奏模式全局变量
# ============================================================
chorus_mode = False
chorus_order = []
chorus_index = 0  # 当前该谁说话
chorus_timer = 0
CHORUS_WORDS = ["祝", "黑", "皮", "神", "话", "哥", "永", "远", "日", "乐", "快", "生"]


def make_transparent_pixmap(path, size=(120, 180)):
    if not HAS_PIL or not os.path.exists(path):
        return QPixmap(path).scaled(*size)
    try:
        img = Image.open(path).convert('RGBA')
        data = img.getdata()
        new = []
        for r, g, b, a in data:
            if r <= 4 and g <= 4 and b <= 4:
                new.append((r, g, b, 0))
            else:
                new.append((r, g, b, a))
        img.putdata(new)
        img = img.resize(size, Image.Resampling.LANCZOS)
        qi = QImage(img.tobytes('raw', 'BGRA'), img.width, img.height,
                   QImage.Format_ARGB32)
        return QPixmap.fromImage(qi)
    except:
        return QPixmap(size[0], size[1])


class PetWindow(QWidget):
    def __init__(self, char_id, pixmap, start_x, start_y, screen_w, screen_h):
        super().__init__()
        self.char_id = char_id
        self.pm_normal = pixmap
        transform = QTransform().scale(-1, 1)
        self.pm_flip = pixmap.transformed(transform)
        self.x = float(start_x)
        self.y = float(start_y)
        self.sw = screen_w
        self.sh = screen_h
        self.W = 120
        self.H = 180
        self.vx = random.uniform(1, 2) * random.choice([-1, 1])
        self.vy = random.uniform(0.5, 1) * random.choice([-1, 1])
        self.facing = self.vx > 0
        self.state = 'walk'
        self.timer_val = 0
        self.bubble_visible = False
        self.bubble_timer = 0
        self.train_speak_timer = 0

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(self.W, self.H)
        self.move(int(start_x), int(start_y))

        self.lbl = QLabel(self)
        self.lbl.setPixmap(self.pm_normal if self.facing else self.pm_flip)
        self.lbl.setGeometry(0, 0, self.W, self.H)

        self.bubble = QLabel("", None, Qt.ToolTip | Qt.FramelessWindowHint | Qt.WA_TranslucentBackground)
        self.bubble.setStyleSheet("background:rgba(255,255,255,.98);border:2px solid #555;border-radius:10px;padding:8px 15px;font-size:16px;color:#222;font-family:'Microsoft YaHei',sans-serif;font-weight:bold;")
        self.bubble.hide()

        # Enable right-click context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_menu)

        t = QTimer(self)
        t.timeout.connect(self.tick)
        t.start(33)
        self.show()

    def paintEvent(self, event):
        pass

    def tick(self):
        global train_mode, recall_mode, potato_mode, chorus_mode
        if potato_mode:
            self._tick_potato()
            return
        if chorus_mode:
            self._tick_chorus()
            return
        if recall_mode:
            self._tick_recall()
            return
        if train_mode:
            self._tick_train()
            return

        PAD = 15
        if self.state == 'walk':
            if random.random() < 0.003:
                self.state = 'pause'
                self.timer_val = random.randint(80, 200)
                return
            if random.random() < 0.005:
                self.vx = -self.vx; self.facing = self.vx > 0
            self.x += self.vx; self.y += self.vy
            if self.x <= PAD:
                self.x = PAD; self.vx = abs(self.vx) * 0.8; self.facing = True
            elif self.x + self.W >= self.sw - PAD:
                self.x = self.sw - self.W - PAD; self.vx = -abs(self.vx) * 0.8; self.facing = False
            if self.y <= PAD:
                self.y = PAD; self.vy = abs(self.vy) * 0.8
            elif self.y + self.H >= self.sh - PAD:
                self.y = self.sh - self.H - PAD; self.vy = -abs(self.vy) * 0.8
            self.lbl.setPixmap(self.pm_normal if self.facing else self.pm_flip)
            self.move(int(self.x), int(self.y))
        elif self.state == 'pause':
            self.timer_val -= 1
            if self.timer_val <= 0:
                self.state = 'walk'
        elif self.state == 'speak':
            self.timer_val -= 1
            if self.timer_val <= 0:
                self.bubble.hide(); self.state = 'walk'
                self.bubble_visible = False

        # Sync bubble position when moving
        if self.state == 'speak':
            self.bubble.move(int(self.x + 60 - self.bubble.width()//2), int(self.y - 50))

    def mouseDoubleClickEvent(self, event):
        """Double click THIS pet first, then others in random order"""
        global train_mode, recall_mode, potato_mode, chorus_mode
        if train_mode or recall_mode or potato_mode or chorus_mode:
            return  # 特殊模式下禁用双击互动

        # Make clicked pet speak first
        self.speak()

        # Get remaining pets (excluding this one)
        others = [p for p in pets if p != self]
        random.shuffle(others)

        # Others speak in random order
        for i, pet in enumerate(others):
            QTimer.singleShot(500 + i * 400, pet.speak)

    def _tick_train(self):
        """火车模式下的每帧更新"""
        global train_mode, train_leader, train_order

        if not train_mode or train_leader is None:
            return

        if self == train_leader:
            # 火车头：跟随鼠标
            cursor_pos = QCursor.pos()
            target_x = cursor_pos.x() - self.W // 2
            target_y = cursor_pos.y() - self.H // 2
            # 限制在屏幕范围内
            target_x = max(0, min(target_x, self.sw - self.W))
            target_y = max(0, min(target_y, self.sh - self.H))
            # 平滑跟随
            self.x += (target_x - self.x) * 0.2
            self.y += (target_y - self.y) * 0.2
            # 根据目标方向更新朝向
            if target_x > self.x + 2:
                self.facing = True
            elif target_x < self.x - 2:
                self.facing = False

            # 自动说话计时器（每4秒 ≈ 121 ticks，33ms/tick）
            self.train_speak_timer -= 1
            if self.train_speak_timer <= 0:
                self.train_speak_timer = 121
                self._speak_train()

            # 气泡跟随
            if self.bubble_visible:
                self.bubble_timer -= 1
                if self.bubble_timer <= 0:
                    self.bubble.hide()
                    self.bubble_visible = False
                else:
                    self.bubble.move(
                        int(self.x + 60 - self.bubble.width() // 2),
                        int(self.y - 50)
                    )
        else:
            # 跟随者：排在前一个角色后面
            idx = train_order.index(self)
            prev_pet = train_order[idx - 1]
            spacing = 135

            if prev_pet.facing:
                target_x = prev_pet.x - spacing
            else:
                target_x = prev_pet.x + spacing
            target_y = prev_pet.y

            # 平滑跟随
            self.x += (target_x - self.x) * 0.12
            self.y += (target_y - self.y) * 0.12
            self.facing = prev_pet.facing

            # 跟随者隐藏气泡
            if self.bubble_visible:
                self.bubble.hide()
                self.bubble_visible = False

        self.lbl.setPixmap(self.pm_normal if self.facing else self.pm_flip)
        self.move(int(self.x), int(self.y))

    def _speak_train(self):
        """火车头随机说一句话"""
        phrase = random.choice(TRAIN_PHRASES)
        self.bubble_visible = True
        self.bubble_timer = 80  # 约2.6秒后消失
        self.bubble.setText(phrase)
        self.bubble.adjustSize()
        self.bubble.move(
            int(self.x + 60 - self.bubble.width() // 2),
            int(self.y - 50)
        )
        self.bubble.show()

    def _tick_recall(self):
        """回城模式：火车驶向桌面右下角，逐个淡出，尾巴留下说话"""
        global recall_mode, recall_order, recall_head_index
        global recall_fading_pet, recall_fade_timer, recall_finished

        if not recall_mode or recall_finished:
            return

        # 我在回城队列中的位置
        if self not in recall_order:
            return
        my_idx = recall_order.index(self)

        # ---- 如果我是正在淡出的角色 ----
        if self == recall_fading_pet:
            recall_fade_timer -= 1
            alpha = max(0.0, recall_fade_timer / 30.0)
            self.setWindowOpacity(alpha)
            if recall_fade_timer <= 0:
                self.hide()
                self.setWindowOpacity(1.0)
                recall_fading_pet = None
                recall_head_index += 1
            return

        # ---- 已隐藏的角色跳过 ----
        if self.isHidden():
            return

        # ---- 在当前头之前（已到达）的角色跳过 ----
        if my_idx < recall_head_index:
            return

        # ---- 当前火车头：驶向目的地 ----
        if my_idx == recall_head_index:
            dx = recall_dest_x - self.x
            dy = recall_dest_y - self.y
            dist = max((dx * dx + dy * dy) ** 0.5, 1)

            if dist < 12:
                # 到达目的地
                if recall_head_index >= len(recall_order) - 1:
                    # 这是尾巴，直接站住说话，不消失
                    self.x = recall_dest_x
                    self.y = recall_dest_y
                    self.facing = False
                    self.lbl.setPixmap(self.pm_flip)
                    self.move(int(self.x), int(self.y))
                    self.speak_custom("呜呜呜~快放我出去玩", duration=200)
                    recall_finished = True
                else:
                    # 不是尾巴，开始淡出
                    recall_fading_pet = self
                    recall_fade_timer = 30
                    self.x = recall_dest_x
                    self.y = recall_dest_y
                return

            speed = 6.0
            move_x = (dx / dist) * speed
            move_y = (dy / dist) * speed
            # 防止越界导致来回振荡
            if abs(move_x) > abs(dx):
                move_x = dx
            if abs(move_y) > abs(dy):
                move_y = dy
            self.x += move_x
            self.y += move_y
            self.facing = dx > 0

        # ---- 跟随者：跟在前面角色后面 ----
        else:
            prev_pet = recall_order[my_idx - 1]
            if prev_pet.isHidden() or prev_pet == recall_fading_pet:
                dx = recall_dest_x - self.x
                dy = recall_dest_y - self.y
                dist = max((dx * dx + dy * dy) ** 0.5, 1)
                speed = 6.0
                move_x = (dx / dist) * speed
                move_y = (dy / dist) * speed
                if abs(move_x) > abs(dx):
                    move_x = dx
                if abs(move_y) > abs(dy):
                    move_y = dy
                self.x += move_x
                self.y += move_y
                self.facing = dx > 0
            else:
                spacing = 135
                target_x = prev_pet.x - spacing if prev_pet.facing else prev_pet.x + spacing
                target_y = prev_pet.y
                self.x += (target_x - self.x) * 0.12
                self.y += (target_y - self.y) * 0.12
                self.facing = prev_pet.facing

        self.lbl.setPixmap(self.pm_normal if self.facing else self.pm_flip)
        self.move(int(self.x), int(self.y))

    def _tick_potato(self):
        """击鼓传康：围成圆圈，高亮快速轮转，最后停在某人身上"""
        global potato_mode, potato_finished, potato_order
        global potato_highlight_idx, potato_rotate_timer, potato_rotate_interval
        global potato_phase, potato_phase_timer, potato_rotation_count
        global potato_circle_cx, potato_circle_cy, potato_circle_r

        if not potato_mode or potato_finished:
            return
        if self not in potato_order:
            return

        my_idx = potato_order.index(self)
        n = len(potato_order)
        angle = (2 * math.pi * my_idx / n) - math.pi / 2
        target_x = potato_circle_cx + potato_circle_r * math.cos(angle) - self.W // 2
        base_y = potato_circle_cy + potato_circle_r * math.sin(angle) - self.H // 2

        # ---- 阶段0：聚拢成圈 ----
        if potato_phase == 0:
            self.x += (target_x - self.x) * 0.18
            self.y += (base_y - self.y) * 0.18
            self.facing = target_x > self.x

        # ---- 阶段1：旋转传康 ----
        elif potato_phase == 1:
            self.x = target_x
            self.y = base_y - (25 if my_idx == potato_highlight_idx else 0)
            self.facing = potato_circle_cx > self.x

        # ---- 阶段2：结束，选定的人说话 ----
        elif potato_phase == 2:
            self.x = target_x
            self.y = base_y
            self.facing = potato_circle_cx > self.x

        self.lbl.setPixmap(self.pm_normal if self.facing else self.pm_flip)
        self.move(int(self.x), int(self.y))

        # ---- 全局阶段计时（只在特定角色中执行一次） ----
        if my_idx != 0:
            return  # 只用第一个角色驱动全局逻辑

        potato_phase_timer -= 1

        if potato_phase == 0:
            if potato_phase_timer <= 0:
                potato_phase = 1
                potato_phase_timer = 9999  # 旋转阶段用其他方式控制
                potato_rotate_timer = potato_rotate_interval

        elif potato_phase == 1:
            potato_rotate_timer -= 1
            if potato_rotate_timer <= 0:
                # 移动到下一个高亮
                potato_highlight_idx = (potato_highlight_idx + 1) % n
                potato_rotation_count += 1
                potato_rotate_timer = potato_rotate_interval

                # 逐渐减速
                if potato_rotation_count % 3 == 0:
                    potato_rotate_interval += 2

                # 间隔够大就停止
                if potato_rotate_interval >= 17:
                    potato_phase = 2
                    potato_phase_timer = 30  # 停顿一下再说话

        elif potato_phase == 2:
            if potato_phase_timer == 30:
                # 让选中的角色在下一帧说话
                pass
            if potato_phase_timer <= 0:
                potato_finished = True
                # 高亮人说主句，其他人说"真的很帅"
                selected = potato_order[potato_highlight_idx]
                selected.speak_custom("都是同龄人我原本没想酱味大鸡！", duration=150)
                others = [p for p in potato_order if p != selected]
                random.shuffle(others)
                for i, p in enumerate(others):
                    QTimer.singleShot(600 + i * 400, lambda pet=p: pet.speak_custom("真的很帅"))

    def _tick_chorus(self):
        """生日祝福大合奏：排成一排，每人依次说一个字"""
        global chorus_mode, chorus_order, chorus_index, chorus_timer

        if not chorus_mode:
            return
        if self not in chorus_order:
            return

        my_idx = chorus_order.index(self)
        n = len(chorus_order)

        # 计算底部排列位置（任务栏上方）
        total_w = n * 135
        start_x = (self.sw - total_w) // 2
        target_x = start_x + my_idx * 135

        # 获取可用工作区，确保站在任务栏上方
        app = QApplication.instance()
        work_area = app.primaryScreen().availableGeometry()
        effective_bottom = work_area.y() + work_area.height()
        target_y = effective_bottom - 200

        # 平滑移动到位置
        self.x += (target_x - self.x) * 0.15
        self.y += (target_y - self.y) * 0.15
        self.facing = target_x > self.x
        self.lbl.setPixmap(self.pm_normal if self.facing else self.pm_flip)
        self.move(int(self.x), int(self.y))

        # ---- 全局计时（只用一个角色驱动） ----
        if my_idx != 0:
            return

        chorus_timer -= 1
        if chorus_timer <= 0 and chorus_index < n:
            pet = chorus_order[chorus_index]
            word = CHORUS_WORDS[chorus_index]
            pet.speak_custom(word, duration=60)
            chorus_index += 1
            chorus_timer = 12  # ~400ms 间隔

        # 全部说完后自动散开
        if chorus_index >= n:
            chorus_timer -= 1  # 继续倒计时（给最后一个人一点时间）
            # 检查最后一个说话结束
            all_done = all(p.state != 'speak' for p in chorus_order)
            if all_done and chorus_timer < -30:
                finish_chorus()

    def _show_menu(self, pos):
        """右键菜单：接火车 / 一键回城 / 击鼓传康 / 生日祝福 / 重新散开 / 退出"""
        global train_mode, recall_mode, recall_finished
        global potato_mode, potato_finished, chorus_mode
        from PyQt5.QtWidgets import QMenu

        menu = QMenu(self)

        # ---- 回城完成后：只显示"放虎归山"和"退出程序" ----
        if recall_mode and recall_finished:
            act_release = menu.addAction("放虎归山")
            menu.addSeparator()
            act_exit = menu.addAction("退出程序")

            selected = menu.exec_(self.mapToGlobal(pos))
            if selected == act_release:
                release_recall()
            elif selected == act_exit:
                QApplication.instance().quit()
            return

        # ---- 击鼓传康结束后：只显示散开和退出 ----
        if potato_mode and potato_finished:
            act_scatter = menu.addAction("重新散开")
            menu.addSeparator()
            act_exit = menu.addAction("退出程序")

            selected = menu.exec_(self.mapToGlobal(pos))
            if selected == act_scatter:
                scatter_and_speak(self)
            elif selected == act_exit:
                QApplication.instance().quit()
            return

        # ---- 正常 / 特殊模式中 菜单 ----
        in_special = recall_mode or train_mode or potato_mode or chorus_mode

        if not in_special:
            act_train = menu.addAction("接火车")
            act_recall = menu.addAction("一键回城")
            act_potato = menu.addAction("击鼓传康")
            act_chorus = menu.addAction("生日祝福")
        elif train_mode:
            act_stop = menu.addAction("停止接火车")

        act_scatter = menu.addAction("重新散开")
        menu.addSeparator()
        act_exit = menu.addAction("退出程序")

        selected = menu.exec_(self.mapToGlobal(pos))

        if not in_special and selected == act_train:
            start_train(self)
        elif not in_special and selected == act_recall:
            start_recall(self)
        elif not in_special and selected == act_potato:
            start_potato()
        elif not in_special and selected == act_chorus:
            start_chorus()
        elif train_mode and selected == act_stop:
            stop_train()
        elif selected == act_scatter:
            scatter_and_speak(self)
        elif selected == act_exit:
            QApplication.instance().quit()

    def speak_custom(self, text, duration=100):
        """用自定义文本说话"""
        try:
            self.state = 'speak'
            self.timer_val = duration
            self.bubble_visible = True
            self.bubble.setText(text)
            self.bubble.adjustSize()
            self.bubble.move(int(self.x + 60 - self.bubble.width()//2), int(self.y - 50))
            self.bubble.show()
        except Exception as e:
            print(f"Error in speak_custom: {e}")

    def speak(self):
        self.speak_custom("黑皮神话哥生日快乐！")


def start_train(leader_pet):
    """启动火车模式"""
    global train_mode, train_leader, train_order
    train_mode = True
    train_leader = leader_pet

    # 火车顺序：火车头第一位，其余角色随机排列
    others = [p for p in pets if p != leader_pet]
    random.shuffle(others)
    train_order = [leader_pet] + others

    # 初始化火车头自动说话计时器
    leader_pet.train_speak_timer = 121

    # 隐藏所有气泡
    for p in pets:
        if p.bubble_visible:
            p.bubble.hide()
            p.bubble_visible = False

    print(f"火车模式已启动！火车头：角色{leader_pet.char_id}，顺序：{[p.char_id for p in train_order]}")


def stop_train():
    """停止火车模式，恢复自由行走"""
    global train_mode, train_leader, train_order
    train_mode = False
    train_leader = None
    train_order = []

    for p in pets:
        p.state = 'walk'
        p.train_speak_timer = 0
        if p.bubble_visible:
            p.bubble.hide()
            p.bubble_visible = False

    print("火车模式已停止")


def start_recall(leader_pet):
    """一键回城：火车驶向桌面右下角，逐个淡出，尾巴留下说话"""
    global recall_mode, recall_finished, recall_order, recall_dest_x, recall_dest_y
    global recall_head_index, recall_fading_pet, recall_fade_timer
    global train_mode

    # 如果正在火车模式，先停止
    if train_mode:
        stop_train()

    recall_mode = True
    recall_finished = False
    recall_head_index = 0
    recall_fading_pet = None
    recall_fade_timer = 0

    # 回城顺序：被点击角色打头，其余随机排列
    others = [p for p in pets if p != leader_pet]
    random.shuffle(others)
    recall_order = [leader_pet] + others

    # 计算目的地：桌面右下角，任务栏上方
    SW = pets[0].sw
    SH = pets[0].sh
    recall_dest_x = SW - 160

    # 获取可用工作区（排除任务栏），确保角色站在任务栏上方
    app = QApplication.instance()
    work_area = app.primaryScreen().availableGeometry()
    effective_bottom = work_area.y() + work_area.height()
    recall_dest_y = effective_bottom - 200  # 角色底部贴在工作区底部上方

    # 重置所有角色状态
    for p in pets:
        p.show()
        p.setWindowOpacity(1.0)
        p.state = 'walk'
        if p.bubble_visible:
            p.bubble.hide()
            p.bubble_visible = False

    print(f"回城模式启动！火车头：角色{leader_pet.char_id}，驶向右下角({recall_dest_x},{recall_dest_y})")


def release_recall():
    """放虎归山：回城完成后重新散开所有角色"""
    global recall_mode, recall_finished, recall_order, recall_fading_pet

    recall_mode = False
    recall_finished = False
    recall_order = []
    recall_fading_pet = None

    for p in pets:
        p.show()
        p.setWindowOpacity(1.0)
        p.state = 'walk'
        if p.bubble_visible:
            p.bubble.hide()
            p.bubble_visible = False

    # 重新散开
    SW = pets[0].sw
    SH = pets[0].sh
    cols, rows = 6, 2
    cell_w = (SW - 150) / cols
    cell_h = (SH - 220) / rows
    for i, pet in enumerate(pets):
        col = i % cols
        row = i // cols
        pet.x = float(random.randint(int(15 + col * cell_w), int((col + 1) * cell_w - 135)))
        pet.y = float(random.randint(int(15 + row * cell_h), int((row + 1) * cell_h - 195)))
        pet.vx = random.uniform(1, 2) * random.choice([-1, 1])
        pet.vy = random.uniform(0.5, 1) * random.choice([-1, 1])
        pet.facing = pet.vx > 0
        pet.move(int(pet.x), int(pet.y))

    # 所有角色随机依次说"我的甲沟好痛"
    random.shuffle(pets)
    for i, pet in enumerate(pets):
        QTimer.singleShot(i * 350, lambda p=pet: p.speak_custom("我的甲沟好痛"))

    print("放虎归山！")


def start_potato():
    """击鼓传康：围成圆圈，高亮快速轮转，停在某人身上"""
    global potato_mode, potato_finished, potato_order
    global potato_highlight_idx, potato_rotate_timer, potato_rotate_interval
    global potato_phase, potato_phase_timer, potato_rotation_count
    global potato_circle_cx, potato_circle_cy, potato_circle_r
    global train_mode, recall_mode

    # 停掉其他模式
    if recall_mode:
        recall_mode = False
        recall_finished = False
        recall_order = []
        recall_fading_pet = None
    if train_mode:
        stop_train()

    potato_mode = True
    potato_finished = False
    potato_phase = 0
    potato_phase_timer = 30  # 聚拢阶段约1秒
    potato_highlight_idx = 0
    potato_rotate_timer = 0
    potato_rotate_interval = 3  # 起始快速
    potato_rotation_count = 0

    # 随机排列
    potato_order = list(pets)
    random.shuffle(potato_order)

    # 圆圈参数：屏幕中央偏上
    SW = pets[0].sw
    SH = pets[0].sh
    potato_circle_cx = SW // 2
    potato_circle_cy = SH // 2 - 80
    potato_circle_r = min(SW // 3, 280)

    # 重置所有角色
    for p in pets:
        p.show()
        p.setWindowOpacity(1.0)
        p.state = 'walk'
        if p.bubble_visible:
            p.bubble.hide()
            p.bubble_visible = False

    print(f"击鼓传康启动！圆圈中心({potato_circle_cx},{potato_circle_cy})，半径{potato_circle_r}")


def start_chorus():
    """生日祝福大合奏：排成一排，每人依次说一个字"""
    global chorus_mode, chorus_order, chorus_index, chorus_timer
    global train_mode, recall_mode, potato_mode

    # 停掉其他模式
    if potato_mode:
        stop_potato()
    if recall_mode:
        recall_mode = False
        recall_finished = False
        recall_order = []
        recall_fading_pet = None
        for p in pets:
            p.show()
            p.setWindowOpacity(1.0)
    if train_mode:
        stop_train()

    chorus_mode = True
    chorus_index = 0
    chorus_timer = 25  # 先让角色到位再开始说话

    # 固定顺序
    chorus_order = list(pets)
    random.shuffle(chorus_order)

    # 重置所有角色
    for p in pets:
        p.show()
        p.setWindowOpacity(1.0)
        p.state = 'walk'
        if p.bubble_visible:
            p.bubble.hide()
            p.bubble_visible = False

    print("生日祝福大合奏启动！")


def stop_potato():
    """停止击鼓传康"""
    global potato_mode, potato_finished, potato_order
    potato_mode = False
    potato_finished = False
    potato_order = []
    for p in pets:
        p.state = 'walk'
        if p.bubble_visible:
            p.bubble.hide()
            p.bubble_visible = False


def finish_chorus():
    """生日祝福完成后自动散开"""
    global chorus_mode, chorus_order, chorus_index
    chorus_mode = False
    chorus_order = []
    chorus_index = 0

    SW = pets[0].sw
    SH = pets[0].sh
    cols, rows = 6, 2
    cell_w = (SW - 150) / cols
    cell_h = (SH - 220) / rows
    for i, pet in enumerate(pets):
        col = i % cols
        row = i // cols
        pet.x = float(random.randint(int(15 + col * cell_w), int((col + 1) * cell_w - 135)))
        pet.y = float(random.randint(int(15 + row * cell_h), int((row + 1) * cell_h - 195)))
        pet.vx = random.uniform(1, 2) * random.choice([-1, 1])
        pet.vy = random.uniform(0.5, 1) * random.choice([-1, 1])
        pet.facing = pet.vx > 0
        pet.state = 'walk'
        pet.move(int(pet.x), int(pet.y))
        if pet.bubble_visible:
            pet.bubble.hide()
            pet.bubble_visible = False

    print("生日祝福完成！")


def scatter_and_speak(clicked_pet):
    """重新散开所有角色，被点击的说"想吃板筋"，其他随机依次说"想吃鸡蛋" """
    global train_mode, train_leader, train_order
    global recall_mode, recall_finished, recall_order, recall_fading_pet
    global potato_mode, potato_finished, potato_order
    global chorus_mode, chorus_order, chorus_index

    # 停止所有特殊模式
    if potato_mode:
        stop_potato()
    if chorus_mode:
        chorus_mode = False
        chorus_order = []
        chorus_index = 0
    if recall_mode:
        recall_mode = False
        recall_finished = False
        recall_order = []
        recall_fading_pet = None
        for p in pets:
            p.show()
            p.setWindowOpacity(1.0)
    if train_mode:
        stop_train()

    # 先隐藏所有气泡
    for p in pets:
        p.bubble.hide()
        p.bubble_visible = False
        p.state = 'walk'

    # 获取屏幕尺寸（所有 pet 存了同样的值）
    SW = pets[0].sw if pets else 1920
    SH = pets[0].sh if pets else 1080

    # 用网格随机分布（6列×2行，适配12个角色）
    cols, rows = 6, 2
    cell_w = (SW - 150) / cols
    cell_h = (SH - 220) / rows

    for i, pet in enumerate(pets):
        col = i % cols
        row = i // cols
        new_x = random.randint(int(15 + col * cell_w), int((col + 1) * cell_w - 135))
        new_y = random.randint(int(15 + row * cell_h), int((row + 1) * cell_h - 195))
        pet.x = float(new_x)
        pet.y = float(new_y)
        pet.vx = random.uniform(1, 2) * random.choice([-1, 1])
        pet.vy = random.uniform(0.5, 1) * random.choice([-1, 1])
        pet.facing = pet.vx > 0
        pet.state = 'walk'
        pet.move(int(pet.x), int(pet.y))

    # 被点击的角色说"想吃板筋"
    clicked_pet.speak_custom("想吃板筋")

    # 其他角色随机排列，依次说"想吃鸡蛋"
    others = [p for p in pets if p != clicked_pet]
    random.shuffle(others)
    for i, pet in enumerate(others):
        QTimer.singleShot(500 + i * 400, lambda p=pet: p.speak_custom("想吃鸡蛋"))


pets = []


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    screen = app.primaryScreen().geometry()
    SW, SH = screen.width(), screen.height()

    # PyInstaller 打包后资源在 sys._MEIPASS 中
    if getattr(sys, 'frozen', False):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.join(base_dir, 'assets')

    cols, rows = 6, 2
    cell_w = (SW - 150) / cols
    cell_h = (SH - 220) / rows

    # Load pic (1) to pic (12)
    char_count = 0
    for i in range(1, 13):
        path = os.path.join(assets_dir, f"pic ({i}).jpg")
        if os.path.exists(path):
            pm = make_transparent_pixmap(path)
            if not pm.isNull():
                col = char_count % cols
                row = char_count // cols
                x = random.randint(int(15 + col * cell_w), int((col + 1) * cell_w - 135))
                y = random.randint(int(15 + row * cell_h), int((row + 1) * cell_h - 195))
                pet = PetWindow(i, pm, x, y, SW, SH)
                pets.append(pet)
                char_count += 1

    print(f"Loaded {len(pets)} pets - Double click to speak")

    try:
        result = app.exec_()
        print(f"App exited with code {result}")
        return result
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())