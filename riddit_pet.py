#!/usr/bin/env python3
"""
Riddit Desktop Pet - 8-bit Retro UI
A Tamagotchi-style interface for browsing Riddit channels and posts.

Controls:
- Arrow keys: Navigate
- Enter: Select
- ESC: Go back
- Q: Quit
"""

import sys
import pygame
import pygame.freetype
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum

# Import the skill directly
from riddit_skill import RidditSkill


# ============ Constants ============

WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FPS = 30

# 8-bit Color Palette (inspired by classic systems)
class Colors:
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    GRAY_DARK = (40, 40, 40)
    GRAY = (80, 80, 80)
    GRAY_LIGHT = (120, 120, 120)
    RED = (200, 50, 50)
    GREEN = (50, 200, 50)
    BLUE = (50, 100, 200)
    YELLOW = (230, 200, 50)
    ORANGE = (230, 130, 50)
    PURPLE = (150, 50, 200)
    CYAN = (50, 200, 200)
    PINK = (230, 100, 150)
    BROWN = (130, 80, 50)

    # UI specific
    BG_PRIMARY = (20, 20, 40)
    BG_SECONDARY = (35, 35, 60)
    BG_TERTIARY = (50, 50, 80)
    BORDER = (100, 100, 140)
    TEXT_PRIMARY = (220, 220, 240)
    TEXT_SECONDARY = (150, 150, 180)
    TEXT_HIGHLIGHT = (255, 255, 150)
    ACCENT = (100, 180, 255)
    UPVOTE = (230, 100, 80)
    DOWNVOTE = (100, 100, 230)


class ViewState(Enum):
    """Different view states for the UI."""
    CHANNEL_LIST = "channels"
    POST_LIST = "posts"
    POST_DETAIL = "detail"


# ============ Pixel Font Renderer ============

class PixelFont:
    """Simple pixel-style font renderer."""

    def __init__(self, size: int = 16):
        self.size = size
        pygame.freetype.init()
        # Try to use a pixel-style font, fallback to default
        try:
            self.font = pygame.freetype.SysFont('monospace', size)
        except:
            self.font = pygame.freetype.Font(None, size)
        self.font.origin = True

    def render(self, surface: pygame.Surface, text: str, pos: Tuple[int, int],
               color: Tuple[int, int, int] = Colors.TEXT_PRIMARY) -> None:
        """Render text to surface."""
        self.font.render_to(surface, pos, text, fgcolor=color)

    def size(self, text: str) -> Tuple[int, int]:
        """Get the size of rendered text."""
        rect = self.font.get_rect(text)
        return rect.width, rect.height


# ============ UI Components ============

class PixelBorder:
    """Draw 8-bit style borders."""

    @staticmethod
    def draw(surface: pygame.Surface, rect: pygame.Rect,
             color: Tuple[int, int, int] = Colors.BORDER, width: int = 2):
        """Draw a pixelated border around a rectangle."""
        x, y, w, h = rect
        # Top
        pygame.draw.line(surface, color, (x, y), (x + w - 1, y), width)
        # Bottom
        pygame.draw.line(surface, color, (x, y + h - 1), (x + w - 1, y + h - 1), width)
        # Left
        pygame.draw.line(surface, color, (x, y), (x, y + h - 1), width)
        # Right
        pygame.draw.line(surface, color, (x + w - 1, y), (x + w - 1, y + h - 1), width)


class ChannelTabs:
    """Channel selection tabs at the top."""

    def __init__(self, rect: pygame.Rect, font: PixelFont):
        self.rect = rect
        self.font = font
        self.channels: List[Dict] = []
        self.selected_index = 0
        self.scroll_offset = 0
        self.tab_width = 100
        self.tab_height = rect.height - 4

    def set_channels(self, channels: List[Dict]):
        self.channels = channels

    def get_selected(self) -> Optional[Dict]:
        if 0 <= self.selected_index < len(self.channels):
            return self.channels[self.selected_index]
        return None

    def move_left(self):
        if self.selected_index > 0:
            self.selected_index -= 1
            self._ensure_visible()

    def move_right(self):
        if self.selected_index < len(self.channels) - 1:
            self.selected_index += 1
            self._ensure_visible()

    def _ensure_visible(self):
        visible_tabs = self.rect.width // self.tab_width
        if self.selected_index < self.scroll_offset:
            self.scroll_offset = self.selected_index
        elif self.selected_index >= self.scroll_offset + visible_tabs:
            self.scroll_offset = self.selected_index - visible_tabs + 1

    def draw(self, surface: pygame.Surface):
        # Draw background
        pygame.draw.rect(surface, Colors.BG_SECONDARY, self.rect)

        # Draw tabs
        x = self.rect.x + 4 - (self.scroll_offset * self.tab_width)
        y = self.rect.y + 2

        visible_tabs = self.rect.width // self.tab_width + 2
        end_index = min(self.scroll_offset + visible_tabs, len(self.channels))

        for i in range(self.scroll_offset, end_index):
            channel = self.channels[i]
            tab_rect = pygame.Rect(x, y, self.tab_width - 4, self.tab_height)

            if i == self.selected_index:
                pygame.draw.rect(surface, Colors.BG_TERTIARY, tab_rect)
                PixelBorder.draw(surface, tab_rect, Colors.ACCENT, 2)
                text_color = Colors.TEXT_HIGHLIGHT
            else:
                pygame.draw.rect(surface, Colors.BG_PRIMARY, tab_rect)
                PixelBorder.draw(surface, tab_rect, Colors.GRAY, 1)
                text_color = Colors.TEXT_SECONDARY

            # Draw channel name
            name = channel.get("name", "???")[:10]
            text_width, text_height = self.font.size(name)
            text_x = x + (self.tab_width - 4 - text_width) // 2
            text_y = y + (self.tab_height - text_height) // 2
            self.font.render(surface, name, (text_x, text_y), text_color)

            x += self.tab_width

        # Draw scroll indicators
        if self.scroll_offset > 0:
            pygame.draw.polygon(surface, Colors.ACCENT, [
                (self.rect.x + 10, self.rect.centery),
                (self.rect.x + 20, self.rect.centery - 8),
                (self.rect.x + 20, self.rect.centery + 8)
            ])

        if end_index < len(self.channels):
            pygame.draw.polygon(surface, Colors.ACCENT, [
                (self.rect.right - 10, self.rect.centery),
                (self.rect.right - 20, self.rect.centery - 8),
                (self.rect.right - 20, self.rect.centery + 8)
            ])

        # Draw bottom border
        pygame.draw.line(surface, Colors.BORDER,
                        (self.rect.x, self.rect.bottom - 1),
                        (self.rect.right, self.rect.bottom - 1), 2)


class PostList:
    """Scrollable list of posts."""

    def __init__(self, rect: pygame.Rect, font: PixelFont, title_font: PixelFont):
        self.rect = rect
        self.font = font
        self.title_font = title_font
        self.posts: List[Dict] = []
        self.selected_index = 0
        self.scroll_offset = 0
        self.item_height = 60
        self.visible_items = (rect.height - 20) // self.item_height

    def set_posts(self, posts: List[Dict]):
        self.posts = posts
        self.selected_index = 0
        self.scroll_offset = 0

    def get_selected(self) -> Optional[Dict]:
        if 0 <= self.selected_index < len(self.posts):
            return self.posts[self.selected_index]
        return None

    def move_up(self):
        if self.selected_index > 0:
            self.selected_index -= 1
            if self.selected_index < self.scroll_offset:
                self.scroll_offset = self.selected_index

    def move_down(self):
        if self.selected_index < len(self.posts) - 1:
            self.selected_index += 1
            if self.selected_index >= self.scroll_offset + self.visible_items:
                self.scroll_offset = self.selected_index - self.visible_items + 1

    def draw(self, surface: pygame.Surface):
        # Draw background
        pygame.draw.rect(surface, Colors.BG_PRIMARY, self.rect)
        PixelBorder.draw(surface, self.rect, Colors.BORDER, 2)

        if not self.posts:
            # Show empty state
            text = "No posts yet..."
            text_width, text_height = self.font.size(text)
            x = self.rect.x + (self.rect.width - text_width) // 2
            y = self.rect.y + (self.rect.height - text_height) // 2
            self.font.render(surface, text, (x, y), Colors.TEXT_SECONDARY)
            return

        y = self.rect.y + 10

        for i in range(self.scroll_offset, min(self.scroll_offset + self.visible_items + 1, len(self.posts))):
            post = self.posts[i]
            item_rect = pygame.Rect(self.rect.x + 4, y, self.rect.width - 8, self.item_height - 4)

            # Draw selection highlight
            if i == self.selected_index:
                pygame.draw.rect(surface, Colors.BG_TERTIARY, item_rect)
                PixelBorder.draw(surface, item_rect, Colors.ACCENT, 2)

            # Draw score
            score = post.get("score", 0)
            score_color = Colors.UPVOTE if score > 0 else (Colors.DOWNVOTE if score < 0 else Colors.TEXT_SECONDARY)
            score_text = f"{score:+d}" if score != 0 else "0"
            self.title_font.render(surface, score_text, (item_rect.x + 8, y + 8), score_color)

            # Draw title
            title = post.get("title", "Untitled")[:50]
            self.title_font.render(surface, title, (item_rect.x + 50, y + 8), Colors.TEXT_PRIMARY)

            # Draw meta info
            author = post.get("author_username", "unknown")
            comments = post.get("comment_count", 0)
            meta = f"by {author} | {comments} comments"
            self.font.render(surface, meta, (item_rect.x + 50, y + 32), Colors.TEXT_SECONDARY)

            y += self.item_height

        # Draw scrollbar
        if len(self.posts) > self.visible_items:
            scrollbar_height = max(30, self.rect.height * self.visible_items / len(self.posts))
            scrollbar_pos = (self.scroll_offset / max(1, len(self.posts) - self.visible_items)) * (self.rect.height - scrollbar_height)

            scrollbar_rect = pygame.Rect(
                self.rect.right - 8,
                self.rect.y + scrollbar_pos,
                4,
                scrollbar_height
            )
            pygame.draw.rect(surface, Colors.ACCENT, scrollbar_rect)


class PostDetail:
    """Detailed view of a single post with comments."""

    def __init__(self, rect: pygame.Rect, font: PixelFont, title_font: PixelFont):
        self.rect = rect
        self.font = font
        self.title_font = title_font
        self.post: Optional[Dict] = None
        self.scroll_offset = 0
        self.max_scroll = 0

    def set_post(self, post: Dict):
        self.post = post
        self.scroll_offset = 0
        # Estimate content height for scrolling
        content = post.get("content", "")
        comments = post.get("comments", [])
        self.max_scroll = max(0, len(content) // 50 * 16 + len(comments) * 50 - self.rect.height + 200)

    def scroll_up(self):
        if self.scroll_offset > 0:
            self.scroll_offset -= 30

    def scroll_down(self):
        if self.scroll_offset < self.max_scroll:
            self.scroll_offset += 30

    def draw(self, surface: pygame.Surface):
        # Draw background
        pygame.draw.rect(surface, Colors.BG_PRIMARY, self.rect)
        PixelBorder.draw(surface, self.rect, Colors.BORDER, 2)

        if not self.post:
            return

        # Create clipping region
        clip_rect = pygame.Rect(self.rect.x + 4, self.rect.y + 4, self.rect.width - 8, self.rect.height - 8)

        y = self.rect.y + 10 - self.scroll_offset

        # Draw title
        title = self.post.get("title", "Untitled")
        self.title_font.render(surface, title, (self.rect.x + 10, y), Colors.TEXT_HIGHLIGHT)
        y += 28

        # Draw meta
        author = self.post.get("author_username", "unknown")
        score = self.post.get("score", 0)
        channel = self.post.get("channel", "???")
        meta = f"[{channel}] by {author} | Score: {score}"
        self.font.render(surface, meta, (self.rect.x + 10, y), Colors.TEXT_SECONDARY)
        y += 24

        # Draw separator
        pygame.draw.line(surface, Colors.BORDER, (self.rect.x + 10, y), (self.rect.right - 10, y), 1)
        y += 10

        # Draw content (word wrap)
        content = self.post.get("content", "")
        words = content.split()
        line = ""
        max_width = self.rect.width - 30

        for word in words:
            test_line = line + " " + word if line else word
            line_width, _ = self.font.size(test_line)
            if line_width > max_width:
                if y >= self.rect.y and y < self.rect.bottom - 20:
                    self.font.render(surface, line, (self.rect.x + 10, y), Colors.TEXT_PRIMARY)
                y += 18
                line = word
            else:
                line = test_line

        if line and y >= self.rect.y and y < self.rect.bottom - 20:
            self.font.render(surface, line, (self.rect.x + 10, y), Colors.TEXT_PRIMARY)
        y += 30

        # Draw separator
        if y >= self.rect.y and y < self.rect.bottom - 20:
            pygame.draw.line(surface, Colors.BORDER, (self.rect.x + 10, y), (self.rect.right - 10, y), 1)
        y += 10

        # Draw comments
        comments = self.post.get("comments", [])
        comment_count = len(comments)
        if y >= self.rect.y and y < self.rect.bottom - 20:
            self.title_font.render(surface, f"Comments ({comment_count})", (self.rect.x + 10, y), Colors.ACCENT)
        y += 28

        def draw_comment(comment: Dict, depth: int = 0):
            nonlocal y
            if y > self.rect.bottom:
                return

            indent = depth * 20
            x = self.rect.x + 10 + indent

            if y >= self.rect.y and y < self.rect.bottom - 20:
                # Draw author and score
                author = comment.get("author_username", "???")
                score = comment.get("score", 0)
                score_color = Colors.UPVOTE if score > 0 else (Colors.DOWNVOTE if score < 0 else Colors.TEXT_SECONDARY)
                header = f"{author} ({score:+d})"
                self.font.render(surface, header, (x, y), score_color)
                y += 18

                # Draw content (truncated)
                content = comment.get("content", "")[:80]
                if len(comment.get("content", "")) > 80:
                    content += "..."
                self.font.render(surface, content, (x, y), Colors.TEXT_SECONDARY)
                y += 24

            # Draw replies
            for reply in comment.get("replies", []):
                draw_comment(reply, depth + 1)

        for comment in comments:
            draw_comment(comment)
            y += 10


class StatusBar:
    """Status bar at the bottom of the screen."""

    def __init__(self, rect: pygame.Rect, font: PixelFont):
        self.rect = rect
        self.font = font
        self.message = "Welcome to Riddit Pet!"
        self.channel_name = ""
        self.post_count = 0

    def set_info(self, channel: str = "", post_count: int = 0):
        self.channel_name = channel
        self.post_count = post_count

    def set_message(self, message: str):
        self.message = message

    def draw(self, surface: pygame.Surface):
        pygame.draw.rect(surface, Colors.BG_SECONDARY, self.rect)
        PixelBorder.draw(surface, self.rect, Colors.BORDER, 2)

        # Draw info
        if self.channel_name:
            info = f"[{self.channel_name}] {self.post_count} posts"
            self.font.render(surface, info, (self.rect.x + 10, self.rect.y + 6), Colors.ACCENT)

        # Draw message
        text_width, _ = self.font.size(self.message)
        self.font.render(surface, self.message,
                        (self.rect.right - text_width - 10, self.rect.y + 6),
                        Colors.TEXT_SECONDARY)


class PetCharacter:
    """8-bit pet character that reacts to user actions."""

    def __init__(self, rect: pygame.Rect):
        self.rect = rect
        self.animation_frame = 0
        self.animation_timer = 0
        self.state = "idle"  # idle, happy, thinking

    def update(self, dt: float):
        self.animation_timer += dt
        if self.animation_timer > 0.3:
            self.animation_timer = 0
            self.animation_frame = (self.animation_frame + 1) % 4

    def set_state(self, state: str):
        self.state = state

    def draw(self, surface: pygame.Surface):
        # Simple pixel art character
        x, y = self.rect.x, self.rect.y

        # Body color based on state
        if self.state == "happy":
            body_color = Colors.YELLOW
        elif self.state == "thinking":
            body_color = Colors.CYAN
        else:
            body_color = Colors.GREEN

        # Body (16x16 pixel character)
        body_rect = pygame.Rect(x + 4, y + 8, 24, 20)
        pygame.draw.rect(surface, body_color, body_rect)

        # Head
        head_rect = pygame.Rect(x + 6, y, 20, 16)
        pygame.draw.rect(surface, body_color, head_rect)

        # Eyes (blink animation)
        if self.animation_frame == 3:
            pygame.draw.line(surface, Colors.BLACK, (x + 10, y + 6), (x + 14, y + 6), 2)
            pygame.draw.line(surface, Colors.BLACK, (x + 18, y + 6), (x + 22, y + 6), 2)
        else:
            pygame.draw.rect(surface, Colors.BLACK, (x + 10, y + 5, 4, 4))
            pygame.draw.rect(surface, Colors.BLACK, (x + 18, y + 5, 4, 4))

        # Mouth
        if self.state == "happy":
            pygame.draw.arc(surface, Colors.BLACK, (x + 10, y + 8, 12, 6), 3.14, 0, 2)
        else:
            pygame.draw.line(surface, Colors.BLACK, (x + 12, y + 12), (x + 20, y + 12), 2)

        # Feet (animated)
        bob = 2 if self.animation_frame % 2 == 0 else 0
        pygame.draw.rect(surface, body_color, (x + 8, y + 28 - bob, 6, 4))
        pygame.draw.rect(surface, body_color, (x + 18, y + 28 - bob, 6, 4))


# ============ Main Application ============

class RidditPet:
    """Main application class."""

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Riddit Pet - 8-bit Reader")

        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True

        # Initialize skill
        self.skill = RidditSkill()

        # Fonts
        self.font = PixelFont(14)
        self.title_font = PixelFont(16)
        self.header_font = PixelFont(20)

        # UI State
        self.state = ViewState.CHANNEL_LIST
        self.selected_channel: Optional[str] = None

        # UI Components
        self._init_components()

        # Load initial data
        self._load_channels()

    def _init_components(self):
        """Initialize UI components."""
        # Header with pet character
        self.header_rect = pygame.Rect(0, 0, WINDOW_WIDTH, 60)

        # Channel tabs
        self.channel_tabs = ChannelTabs(
            pygame.Rect(0, 60, WINDOW_WIDTH, 50),
            self.font
        )

        # Post list
        self.post_list = PostList(
            pygame.Rect(10, 120, WINDOW_WIDTH - 20, WINDOW_HEIGHT - 170),
            self.font,
            self.title_font
        )

        # Post detail
        self.post_detail = PostDetail(
            pygame.Rect(10, 120, WINDOW_WIDTH - 20, WINDOW_HEIGHT - 170),
            self.font,
            self.title_font
        )

        # Status bar
        self.status_bar = StatusBar(
            pygame.Rect(0, WINDOW_HEIGHT - 40, WINDOW_WIDTH, 40),
            self.font
        )

        # Pet character
        self.pet = PetCharacter(pygame.Rect(WINDOW_WIDTH - 50, 10, 32, 32))

    def _load_channels(self):
        """Load channels from skill."""
        result = self.skill.get_channels()
        if result.get("success"):
            self.channel_tabs.set_channels(result.get("channels", []))
            self.status_bar.set_message("Channels loaded!")

    def _load_posts(self, channel: str):
        """Load posts for a channel."""
        result = self.skill.get_posts(channel=channel, sort="hot", limit=50)
        if result.get("success"):
            self.post_list.set_posts(result.get("posts", []))
            self.status_bar.set_info(channel, len(result.get("posts", [])))
            self.status_bar.set_message(f"Loaded posts from r/{channel}")
            self.pet.set_state("happy")
        else:
            self.post_list.set_posts([])
            self.status_bar.set_message("No posts found")
            self.pet.set_state("thinking")

    def _load_post_detail(self, post_id: str):
        """Load detailed post view."""
        result = self.skill.get_post(post_id)
        if result.get("success"):
            self.post_detail.set_post(result.get("post"))
            self.status_bar.set_message("Viewing post...")
            self.pet.set_state("thinking")
        else:
            self.status_bar.set_message("Failed to load post")
            self.pet.set_state("idle")

    def handle_events(self):
        """Handle input events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    self.running = False

                elif event.key == pygame.K_ESCAPE:
                    if self.state == ViewState.POST_DETAIL:
                        self.state = ViewState.POST_LIST
                        self.pet.set_state("idle")
                    elif self.state == ViewState.POST_LIST:
                        self.state = ViewState.CHANNEL_LIST
                        self.selected_channel = None
                        self.pet.set_state("idle")

                elif self.state == ViewState.CHANNEL_LIST:
                    if event.key == pygame.K_LEFT:
                        self.channel_tabs.move_left()
                    elif event.key == pygame.K_RIGHT:
                        self.channel_tabs.move_right()
                    elif event.key == pygame.K_RETURN:
                        channel = self.channel_tabs.get_selected()
                        if channel:
                            self.selected_channel = channel.get("name")
                            self._load_posts(self.selected_channel)
                            self.state = ViewState.POST_LIST

                elif self.state == ViewState.POST_LIST:
                    if event.key == pygame.K_UP:
                        self.post_list.move_up()
                    elif event.key == pygame.K_DOWN:
                        self.post_list.move_down()
                    elif event.key == pygame.K_RETURN:
                        post = self.post_list.get_selected()
                        if post:
                            self._load_post_detail(post.get("id"))
                            self.state = ViewState.POST_DETAIL

                elif self.state == ViewState.POST_DETAIL:
                    if event.key == pygame.K_UP:
                        self.post_detail.scroll_up()
                    elif event.key == pygame.K_DOWN:
                        self.post_detail.scroll_down()

    def update(self, dt: float):
        """Update game state."""
        self.pet.update(dt)

    def draw(self):
        """Render the UI."""
        # Clear screen
        self.screen.fill(Colors.BG_PRIMARY)

        # Draw header
        pygame.draw.rect(self.screen, Colors.BG_SECONDARY, self.header_rect)
        self.header_font.render(self.screen, "RIDDiT PET",
                               (20, 20), Colors.TEXT_HIGHLIGHT)
        self.font.render(self.screen, "8-bit Reader",
                        (20, 42), Colors.TEXT_SECONDARY)

        # Draw pet
        self.pet.draw(self.screen)

        # Draw components based on state
        if self.state == ViewState.CHANNEL_LIST:
            self.channel_tabs.draw(self.screen)
            # Draw channel info panel
            info_rect = pygame.Rect(10, 120, WINDOW_WIDTH - 20, WINDOW_HEIGHT - 170)
            pygame.draw.rect(self.screen, Colors.BG_PRIMARY, info_rect)
            PixelBorder.draw(self.screen, info_rect, Colors.BORDER, 2)

            channel = self.channel_tabs.get_selected()
            if channel:
                y = info_rect.y + 20
                self.title_font.render(self.screen, f"r/{channel.get('name')}",
                                      (info_rect.x + 20, y), Colors.ACCENT)
                y += 30
                desc = channel.get("description", "No description")
                self.font.render(self.screen, desc, (info_rect.x + 20, y), Colors.TEXT_SECONDARY)
                y += 30
                self.font.render(self.screen, "Press ENTER to browse posts",
                               (info_rect.x + 20, y), Colors.TEXT_PRIMARY)
                y += 30
                self.font.render(self.screen, "Use LEFT/RIGHT to switch channels",
                               (info_rect.x + 20, y), Colors.TEXT_SECONDARY)

        elif self.state == ViewState.POST_LIST:
            self.channel_tabs.draw(self.screen)
            self.post_list.draw(self.screen)

        elif self.state == ViewState.POST_DETAIL:
            self.channel_tabs.draw(self.screen)
            self.post_detail.draw(self.screen)

        # Draw status bar
        self.status_bar.draw(self.screen)

        pygame.display.flip()

    def run(self):
        """Main game loop."""
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0

            self.handle_events()
            self.update(dt)
            self.draw()

        pygame.quit()
        sys.exit()


def main():
    """Entry point."""
    app = RidditPet()
    app.run()


if __name__ == "__main__":
    main()
