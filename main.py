from xarp.express import SyncXR
from xarp.server import run, show_qrcode_link
from xarp.entities import Element, ImageAsset, GLBAsset, DefaultAssets, TextAsset
from xarp.spatial import Transform, Vector3, Pose
from xarp.gestures import INDEX_TIP, THUMB_METACARPAL, MIDDLE_METACARPAL, pinch, PALM, open_hand, flat_palm
from xarp.spatial import Quaternion
from xarp.data_models import Hands
from PIL import Image
import math
import numpy as np

from typing import Tuple

WHITE = (1,1,1,1)
RED = (1,0,0,1)
TRANSPARENT = (1,1,1,.5)
INVISIBLE = (0,0,0,0)

def distance(a: Vector3, b: Vector3):
    return math.sqrt((a.x - b.x)**2 + (a.y - b.y)**2 + (a.z - b.z)**2)

def sq_horz_mag(v: Vector3):
    return v.x**2 + v.z**2

def sq_mag(v: Vector3):
    return v.x**2 + v.y**2 + v.z**2

def hand_normal_similarity(hands: Hands) -> float:
    n_1 = hand_normal(hands.left)
    n_2 = hand_normal(hands.right)

    return np.dot(n_1.to_numpy(), -n_2.to_numpy())

def hand_up_dist(hand: Tuple[Pose, ...]) -> float:
    n = hand_normal(hand)

    a: Vector3 = Vector3.up()
    return np.dot(n.to_numpy(), a.to_numpy())

def hand_normal(hand: Tuple[Pose, ...]) -> Vector3:
    palm = hand[PALM].position
    index = hand[MIDDLE_METACARPAL].position
    thumb = hand[THUMB_METACARPAL].position

    a = index - palm
    b = thumb - palm

    crossed = np.cross(a.to_numpy(), b.to_numpy())
    norm = np.linalg.norm(crossed)
    normalized = crossed if norm == 0 else crossed / norm
    return Vector3(normalized)

#get the vertial position of the table 
def get_table_pos(xr: SyncXR) -> Vector3:
    MESSAGE = """
            Face forward and place your palms face down on the table in front of you.
            Hold still until the message disappears.
            """

    tutorial = Element(
        key = "tutorial",
    )

    left_indicator = Element(
        key = "left_ind",
        transform = Transform(
            scale = Vector3.one() * 0.05
        ),
        asset = DefaultAssets.SPHERE,
        color = INVISIBLE
    )

    right_indicator = Element(
        key = "right_ind",
        transform = Transform(
            scale = Vector3.one() * 0.05
        ),
        asset = DefaultAssets.SPHERE,
        color = INVISIBLE
    )

    table_pos: Vector3 = Vector3.zero()
    nframes = 0
    stream = xr.sense(eye=True, hands=True)
    for frame in stream:

        hands: Hands = frame['hands']
        if not (hands.right and hands.left):
            nframes = 0
            continue
        
        # tutorial.transform.position = frame['eye'].position + Vector3.from_xyz(0, 0, +0.5)
        tutorial.transform.position = (hands.left[PALM].position + hands.right[PALM].position) * .5
        tutorial.asset = TextAsset.from_obj(f"{nframes} \n {MESSAGE}")
        xr.update(tutorial)

        left_down: bool = open_hand(hands.left) and hand_up_dist(hands.left) < -.8
        right_down: bool = open_hand(hands.right) and hand_up_dist(hands.right) > .8

        if left_down and left_indicator.color == INVISIBLE:
            left_indicator.color = WHITE
            xr.update(left_indicator)
        
        if not left_down and left_indicator.color == WHITE:
            left_indicator.color = INVISIBLE
            xr.update(left_indicator)

        if right_down and right_indicator.color == INVISIBLE:
            right_indicator.color = WHITE
            xr.update(right_indicator)

        if not right_down and right_indicator.color == WHITE:
            right_indicator.color = INVISIBLE
            xr.update(right_indicator)

        if not left_down or not right_down:
            nframes = 0
            continue

        y_dist = abs(hands.left[PALM].position.y - hands.right[PALM].position.y)
        if y_dist > .03:
            nframes = 0
            continue

        # if hand_normal_similarity(hands) < .8:
        #     nframes = 0
        #     continue

        # print(f"left: {hand_normal(hands.left)}, right: {hand_normal(hands.right)}")
        # print(f"{hand_normal_dist(hands)}")

        print(f"left: {hand_up_dist(hands.left)}, right: {hand_up_dist(hands.right)}")
        nframes += 1
        # if nframes > 20:
        #     table_pos = hands.right[PALM].position
        #     break

    xr.destroy_element(tutorial)
    stream.close()
    return table_pos

def show_wheel(elements: list[Element], origin: Vector3):
    RADIUS = 0.1
    for i in range(len(elements)):
        elements[i].color = WHITE

        angle = i * (2 * math.pi / len(elements)) + (math.pi / 2)
        x = math.cos(angle) * RADIUS
        y = math.sin(angle) * RADIUS
        elements[i].transform.position.x = origin.x + x
        elements[i].transform.position.y = origin.y + y
        elements[i].transform.position.z = origin.z

def hide_wheel(elements: list[Element]):
    for i in range(len(elements)):
        elements[i].color = INVISIBLE
        elements[i].transform.position = Vector3.zero()

def main(xr: SyncXR, params: dict):
     
    # Have the user place their hand on the table to record its postion
    initial_rh_pos: Vector3 = get_table_pos(xr)

    #import GLB assets
    HEART_ASSET = GLBAsset()
    with open("assets/heart.glb", "rb") as f:
        HEART_ASSET.raw = f.read()
    
    WRENCH_ASSET = GLBAsset()
    with open("assets/wrench.glb", "rb") as f:
        WRENCH_ASSET.raw = f.read()
        
    ALLEN_WRENCH_ASSET = GLBAsset()
    with open("assets/allen_wrench_2.glb", "rb") as f:
        ALLEN_WRENCH_ASSET.raw = f.read()
        
    RATCHET_WRENCH_ASSET = GLBAsset()
    with open("assets/ratchet_wrench.glb", "rb") as f:
        RATCHET_WRENCH_ASSET.raw = f.read()
           
    BIKE_SEAT = GLBAsset()
    with open("assets/bike_seat.glb", "rb") as f:
        BIKE_SEAT.raw = f.read()
        
    ARROW_ASSET = GLBAsset()
    with open("assets/arrow.glb", "rb") as f:
        ARROW_ASSET.raw = f.read()
    
    FRAME_ASSET_1 = ImageAsset.from_obj(obj = Image.open("assets/video_frame1.png"))
    FRAME_ASSET_2 = ImageAsset.from_obj(obj = Image.open("assets/video_frame2.png"))
    
    WRENCH_GUIDE_ASSET = ImageAsset.from_obj(obj = Image.open("assets/wrench_guide.jpg"))
    ALLEN_WRENCH_GUIDE_ASSET = ImageAsset.from_obj(obj = Image.open("assets/allen_wrench_guide.png"))
    RATCHET_WRENCH_GUIDE_ASSET = ImageAsset.from_obj(obj = Image.open("assets/ratchet_wrench_guide.jpg"))
    
    
    # CUBE_WHEEL = GLBAsset()
    # with open("assets/arrow.glb", "rb") as f:
    #     ARROW_ASSET.raw = f.read()

    wheel = [Element(
        key = f'wh_0',
        transform = Transform(
            position = Vector3.zero(),
            scale = Vector3.one() * 0.005,
            rotation = Quaternion.from_euler_angles(90, 0, 90)
        ),
        asset = WRENCH_ASSET
    ), Element(
        key = f'wh_1',
        transform = Transform(position = Vector3.zero(), scale = Vector3.one() * 0.001),
        asset = ALLEN_WRENCH_ASSET
    ), Element(
        key = f'wh_2',
        transform = Transform(
            position = Vector3.zero(), 
            scale = Vector3.one() * 0.45,
            rotation = Quaternion.from_euler_angles(0, -90, 0)
        ),
        asset = RATCHET_WRENCH_ASSET
    )]

    for e in wheel:
        xr.update(e)
        e.asset = None
  
    wrench_element = Element(
        key = f'wrench',
        transform = Transform(
            position = Vector3.from_xyz(initial_rh_pos.x, initial_rh_pos.y + .05, initial_rh_pos.z),
            scale = Vector3.one() * 0.0005,
        ),
        color = TRANSPARENT,
        asset = DefaultAssets.SPHERE
    )
    xr.update(wrench_element)
    
    panel_screen = Element(
        key = 'panel',
        transform = Transform(
            position = Vector3.from_xyz(initial_rh_pos.x-.6, initial_rh_pos.y + 0.2, initial_rh_pos.z + 0.35), # +y is up, -y is down, +z is away from user (forward)
            scale = Vector3.one() * 0.6,
            rotation = Quaternion.from_euler_angles(0, -27.5, 0)
        ),
        asset = ImageAsset.from_obj(obj = Image.open('assets/bike-seat-diagram.jpg')),
        color = WHITE
    )
    xr.update(panel_screen)
    panel_screen.asset = None
    
    active_screen: Element = panel_screen
    active_screen_loc: Vector3 = panel_screen.transform.position

    wrench_screen = Element( # wrench screens appear in the event a menu item was dragged to the panel
        key = 'wrench_screen',
        transform = Transform(
            position = Vector3.zero(), 
            scale = Vector3.one() * 2,
        ),
        asset = WRENCH_GUIDE_ASSET,
        color = INVISIBLE
    )
    xr.update(wrench_screen)
    wrench_screen.asset = None

    ratchet_wrench_screen = Element(
        key = 'ratchet_wrench_screen',
        transform = Transform(
            position = Vector3.zero(), 
            scale = Vector3.one() * 2.5,
        ),
        asset = RATCHET_WRENCH_GUIDE_ASSET,
        color = INVISIBLE
    )
    xr.update(ratchet_wrench_screen)
    ratchet_wrench_screen.asset = None

    ratchet_wrench_screen.transform.scale = Vector3.one() * 2.5
    xr.update(ratchet_wrench_screen)
    
    allen_wrench_screen = Element(
        key = 'allen_wrench_screen',
        transform = Transform(
            position = Vector3.zero(), 
            scale = Vector3.one() * 0.4,
        ),
        asset = ALLEN_WRENCH_GUIDE_ASSET,
        color = INVISIBLE
    )
    xr.update(allen_wrench_screen)
    allen_wrench_screen.asset = None

    allen_wrench_screen.transform.scale = Vector3.one() * .4
    xr.update(allen_wrench_screen)

    idea = Element(
        key = 'idea',
        transform = Transform(
            position = Vector3.zero(),
            scale = Vector3.one(),
            rotation = Quaternion.from_euler_angles(0, 60, 0)
        ),
        asset = BIKE_SEAT,
        color = INVISIBLE
    )
    xr.update(idea)
    idea.asset = None

    idea.transform.scale = Vector3.one() * 0.15
    xr.update(idea)


    idea_shown: bool = False
    idea_held: int = 0

    stream = xr.sense(hands=True)
    
    #define panels for video frames
    panel_frame_1 = Element(
        key = 'frame1',
        transform = Transform(
            position = Vector3.from_xyz(initial_rh_pos.x - 0.15, initial_rh_pos.y+0.15, initial_rh_pos.z + 0.5), 
            scale = Vector3.one() * 0.35,
        ),
        asset = FRAME_ASSET_1,
        color = INVISIBLE
    )
    xr.update(panel_frame_1)
    panel_frame_1.asset = None

    panel_frame_2 = Element(
        key = 'frame2',
        transform = Transform(
            position = Vector3.from_xyz(initial_rh_pos.x - 0.15, initial_rh_pos.y+0.15, initial_rh_pos.z + 0.5), 
            scale = Vector3.one() * 0.35,
        ),
        asset = FRAME_ASSET_2,
        color = INVISIBLE
    )
    xr.update(panel_frame_2)
    panel_frame_2.asset = None

    close_element = Element(
        key = 'close',
        transform = Transform(
            position = Vector3.zero(),
            scale = Vector3.one() * 0.05
        ),
        asset = DefaultAssets.SPHERE,
        color = INVISIBLE
    )

    idea_dragged_to_table: bool = False

    wheel_shown: bool = False
    wheel_held: list[int] = [0, 0, 0]
    wheel_coords = [Vector3.from_xyz(0,0,0), Vector3.from_xyz(0,0,0), Vector3.from_xyz(0,0,0)]
    
    can_cancel: bool = False

    pinched_last_frame: bool = False
    new_pinch: bool = False

    xr.update(wrench_element)
    for frame in stream:

        if not pinched_last_frame and frame['hands'].right and pinch(frame['hands'].right):
            new_pinch = True
            pinched_last_frame = True
        else:
            new_pinch = False
            if frame['hands'].right and not pinch(frame['hands'].right):
                pinched_last_frame = False

        # Handle spawning of idea.
        if not idea_shown and new_pinch and ui_button(panel_screen, frame, .2):
            idea_shown = True
            idea.transform.position = frame['hands'].right[INDEX_TIP].position
            idea.color = WHITE
        
        # Handle dragging of "idea."
        if idea_shown:
            idea_held = ui_drag(idea, frame, .1, idea_held)
            if idea.transform.position.y <= initial_rh_pos.y:
                idea_shown = False
                idea.color = INVISIBLE
                idea.transform.position = Vector3.zero()
                
                timer = 0
                idea_dragged_to_table = True

                wrench_pos = wrench_element.transform.position
                arrow = Element(
                    key = 'arrow',
                    transform = Transform(
                        position = Vector3.from_xyz(wrench_pos.x + -0.3, wrench_pos.y -0.3, wrench_pos.z + 0.1),
                        scale = Vector3.one() * 0.05
                    ),
                    asset = ARROW_ASSET
                )
                xr.update(arrow)
            xr.update(idea)

        # Draw "video."
        if idea_dragged_to_table:
            if timer / 10 == timer // 10:
                if (timer // 10) % 2 == 0:
                    panel_frame_1.color = WHITE
                    panel_frame_2.color = INVISIBLE
                    xr.update(panel_frame_1)
                    xr.update(panel_frame_2)
                else:
                    panel_frame_1.color = INVISIBLE
                    panel_frame_2.color = WHITE

                    # frame 2 needs to be drawn before frame 1 is removed, else there is a moment when
                    # nothing is displayed
                    xr.update(panel_frame_2)
                    xr.update(panel_frame_1)
            timer += 1
            
        if not wheel_shown and new_pinch and ui_button(wrench_element, frame, 0.1):
            show_wheel(wheel, 
                       wrench_element.transform.position 
                            + Vector3.from_xyz(0, 0.2, 0))
            
            for i, e in enumerate(wheel):
                wheel_coords[i] = e.transform.position
                xr.update(e)

            wheel_shown = True
            
        if wheel_shown and frame['hands'].right:
            hands: Hands = frame['hands']
            
            i: int = -1
            for idx, wh in enumerate(wheel_held):
                if wh > 0:
                    i = idx
                    break

            if i >= 0:
                wheel_held[i] = ui_drag(e, frame, 0.1, wheel_held[i])
                if wheel_held[i] == 0:
                    if distance(wheel[i].transform.position, active_screen.transform.position) < .2:
                        screens = [wrench_screen, allen_wrench_screen, ratchet_wrench_screen]
                        active_screen_loc = active_screen.transform.position
                        # next render the new panel and remove the old
                        active_screen.color = INVISIBLE
                        active_screen.transform.position = Vector3.zero()
                        xr.update(active_screen)

                        screens[i].color = WHITE
                        screens[i].transform.position = active_screen_loc
                        screens[i].transform.rotation = active_screen.transform.rotation
                        xr.update(screens[i])

                        active_screen = screens[i]
                        
                    wheel[i].transform.position = wheel_coords[i]
                xr.update(e)
            else:
                for i, e in enumerate(wheel):
                    wheel_held[i] = ui_drag(e, frame, 0.1, wheel_held[i])
                    if wheel_held[i] > 0:
                        xr.update(e)
                        break
                
            # Handle wheel close.
            v: Vector3 = hands.right[PALM].position - wrench_element.transform.position
            if not (sq_horz_mag(v) < .01 and open_hand(hands.right)):
                can_cancel = False
                close_element.transform.position = Vector3.zero()
                close_element.color = INVISIBLE
                xr.update(close_element)
            else:
                # Enable closing when hand is high enough.
                if v.y > 0.3:
                    close_element.color = RED                
                    can_cancel = True

                # If closing is enabled, close when hand reaches low enough y-threshold.
                if can_cancel:
                    close_element.transform.position = hands.right[PALM].position + Vector3.from_xyz(0, -0.02, 0)
                    close_element.color = (1, (.3 - v.y) / .3, (.3 - v.y) / .3, 1)

                    if v.y <= .02:
                        can_cancel = False
                        close_element.transform.position = Vector3.zero()
                        close_element.color = INVISIBLE
                        
                        hide_wheel(wheel)
                    
                        for e in wheel:
                            xr.update(e)

                        wheel_shown = False

                        # Revert active screen to default.
                        active_screen.color = INVISIBLE
                        active_screen.transform.position = Vector3.zero()
                        xr.update(active_screen)

                        panel_screen.color = WHITE
                        panel_screen.transform.position = active_screen_loc
                        xr.update(panel_screen)

                        active_screen = panel_screen

                    xr.update(close_element)
            

    stream.close()

# doesn't seem to work?
# def element_update(xr: SyncXR, element: Element): #update element asset such that it is only fetched once
#     # if not element.asset == None:
#     #     element.asset = None
#     xr.update(element)

# Return true if an element is pinched by the right hand.
def ui_button(button: Element, frame: dict, radius: float,) -> bool:
    hands: Hands = frame['hands']
    if (not hands.right):
        # button.color = WHITE
        return False

    handpos = hands.right[INDEX_TIP].position
    if distance(handpos, button.transform.position) < radius:
        # button.color = RED
        return pinch(hands.right)
    
    # button.color = WHITE
    return False

# Return number greater than 0 if element is held down.
# Pass held state to prevent pinch from decoupling from element mid-movement
def ui_held(ui: Element, frame: dict, radius: float, extra_frames: int):
    FRAMES = 2
    
    hands: Hands = frame['hands']
    if (not hands.right):
        # if (extra_frames == 0):
            # ui.color = WHITE
        return max(0, extra_frames - 1)

    handpos = hands.right[INDEX_TIP].position
    if distance(handpos, ui.transform.position) < radius:
        # ui.color = RED
        if pinch(hands.right):
            return FRAMES
        
    if extra_frames > 0:
        if pinch(hands.right):
            return FRAMES
        else:
            return extra_frames - 1

    # ui.color = WHITE
    return 0

def ui_drag(ui: Element, frame: dict, radius: float, extra_frames: int):
    ret: int = ui_held(ui, frame, radius, extra_frames)
    if ret > 0 and frame['hands'].right:
        ui.transform.position = frame['hands'].right[INDEX_TIP].position
    return ret


if __name__ == "__main__":
    show_qrcode_link()
    run(main)
