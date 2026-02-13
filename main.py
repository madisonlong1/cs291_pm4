from xarp.express import SyncXR
from xarp.server import run, show_qrcode_link
from xarp.entities import Element, ImageAsset, GLBAsset, DefaultAssets
from xarp.spatial import Transform, Vector3, Pose
from xarp.gestures import INDEX_TIP, pinch, PALM, open_hand, flat_palm
from xarp.spatial import Quaternion
from xarp.data_models import Hands
from PIL import Image
import math

WHITE = (1,1,1,1)
RED = (1,0,0,1)
INVISIBLE = (0,0,0,0)

def distance(a: Vector3, b: Vector3):
    return math.sqrt((a.x - b.x)**2 + (a.y - b.y)**2 + (a.z - b.z)**2)

#get the vertial position of the table 
def get_table_pos(xr: SyncXR) -> Vector3:
    table_pos: Vector3 = Vector3.zero()
    nframes = 0
    stream = xr.sense(hands=True)
    for frame in stream:

        hands: Hands = frame['hands']
        if not (hands.right and open_hand(hands.right) and hands.left and open_hand(hands.left)):
            nframes = 0
            continue

        nframes += 1
        if nframes > 20:
            table_pos = hands.right[PALM].position
            break
    stream.close()
    return table_pos

def show_wheel(elements: list[Element], origin: Vector3):
    RADIUS = 0.2
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
    table_pos: Vector3 = get_table_pos(xr)

    #import GLB assets
    HEART_ASSET = GLBAsset()
    with open("assets/heart.glb", "rb") as f:
        HEART_ASSET.raw = f.read()
    
    WRENCH_ASSET = GLBAsset()
    with open("assets/wrench.glb", "rb") as f:
        WRENCH_ASSET.raw = f.read()
        
           
    SEAT_ASSET_3 = GLBAsset()
    with open("assets/bike_seat_3.glb", "rb") as f:
        SEAT_ASSET_3.raw = f.read()
        
    ARROW_ASSET = GLBAsset()
    with open("assets/arrow.glb", "rb") as f:
        ARROW_ASSET.raw = f.read()
    
    FRAME_ASSET_1 = ImageAsset.from_obj(obj = Image.open("assets/video_frame1.png"))
    FRAME_ASSET_2 = ImageAsset.from_obj(obj = Image.open("assets/video_frame2.png"))
    
    
    # CUBE_WHEEL = GLBAsset()
    # with open("assets/arrow.glb", "rb") as f:
    #     ARROW_ASSET.raw = f.read()


    eyepos = xr.eye().position

    wrench_wheel = []

  
    wrench_element = Element(
        key = f'wrench',
        transform = Transform(
            position = Vector3.from_xyz(table_pos.x, table_pos.y, table_pos.z),
            scale = Vector3.one() * 0.01,
        ),
        asset = WRENCH_ASSET
    )

    xr.update(wrench_element)
    wrench_element.asset = None
    
    panel_screen = Element(
        key = 'panel',
        transform = Transform(
            position = Vector3.from_xyz(eyepos.x, eyepos.y - 0.2, eyepos.z + 0.5), # +y is up, -y is down, +z is away from user (forward)
            scale = Vector3.one() * 0.6,
        ),
        asset = ImageAsset.from_obj(obj = Image.open('assets/bike-seat-diagram.jpg')),
        color = WHITE
    )
    xr.update(panel_screen)
    panel_screen.asset = None

    idea = Element(
        key = 'idea',
        transform = Transform(
            position = Vector3.zero(),
            scale = Vector3.one() * 0.15,
        ),
        asset = DefaultAssets.CUBE,
        color = INVISIBLE
    )


    idea_shown: bool = False
    idea_held: bool = False

    stream = xr.sense(hands=True)
    
    #define panels for video frames
    panel_frame_1 = Element(
        key = 'frame1',
        transform = Transform(
            position = Vector3.from_xyz(eyepos.x + 0.8, eyepos.y-0.1, eyepos.z + 0.3), 
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
            position = Vector3.from_xyz(eyepos.x + 0.8, eyepos.y-0.1, eyepos.z + 0.3), 
            scale = Vector3.one() * 0.35,
        ),
        asset = FRAME_ASSET_2,
        color = INVISIBLE
    )
    xr.update(panel_frame_2)
    panel_frame_2.asset = None

    dragged_to_table: bool = False

    for frame in stream:
        if (not idea_shown) and ui_button(panel_screen, frame, .3):
            print('hi')   
            idea_shown = True
            idea.transform.position = frame['hands'].right[INDEX_TIP].position
            idea.color = WHITE
        
        if idea_shown:
            idea_held = ui_drag(idea, frame, .1, idea_held)

        xr.update(idea)
        xr.update(wrench_element)
        
        # if the user drags 'idea' from the panel to the y postion of the table, 
        # this triggers the arrow and video to appear
        if idea_shown and idea.transform.position.y <= table_pos.y:
            idea_shown = False
            idea.color = INVISIBLE
            idea.transform.position = Vector3.zero()
            
            timer = 0
            dragged_to_table = True

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

        if dragged_to_table:
            if timer / 5 == timer // 5:
                if (timer // 5) % 2 == 0:
                    print("1")
                    panel_frame_1.color = WHITE
                    panel_frame_2.color = INVISIBLE
                    xr.update(panel_frame_1)
                    xr.update(panel_frame_2)
                else:
                    print("2")
                    panel_frame_1.color = INVISIBLE
                    panel_frame_2.color = WHITE

                    # frame 2 needs to be drawn before frame 1 is removed, else there is a moment when
                    # nothing is displayed
                    xr.update(panel_frame_2)
                    xr.update(panel_frame_1)
            timer += 1
            
            
            
        # TBD: We will implement the logic to make the menu wheel appear/dissape
        show_wheel()

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
        button.color = WHITE
        return False

    handpos = hands.right[INDEX_TIP].position
    if distance(handpos, button.transform.position) < radius:
        button.color = RED
        return pinch(hands.right)
    
    button.color = WHITE
    return False

# Return true if element is held down.
# Pass held state to prevent pinch from decoupling from element mid-movement
def ui_held(ui: Element, frame: dict, radius: float, was_held: bool):
    hands: Hands = frame['hands']
    if (not hands.right):
        if (not was_held):
            ui.color = WHITE
        return was_held

    if (was_held and pinch(hands.right)):
        return True

    handpos = hands.right[INDEX_TIP].position
    if distance(handpos, ui.transform.position) < radius:
        ui.color = RED
        return pinch(hands.right)
    
    ui.color = WHITE
    return False

def ui_drag(ui: Element, frame: dict, radius: float, was_held: bool):
    held: bool = ui_held(ui, frame, radius, was_held)
    if held:
        ui.transform.position = frame['hands'].right[INDEX_TIP].position
    return held


if __name__ == "__main__":
    show_qrcode_link()
    run(main)
