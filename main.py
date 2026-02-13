from xarp.express import SyncXR
from xarp.server import run, show_qrcode_link
from xarp.entities import Element, ImageAsset, GLBAsset, DefaultAssets
from xarp.spatial import Transform, Vector3, Pose
from xarp.gestures import INDEX_TIP, pinch
from xarp.spatial import Quaternion
from xarp.data_models import Hands
from PIL import Image
import math

WHITE = (1,1,1,1)
RED = (1,0,0,1)
INVISIBLE = (0,0,0,0)

def distance(a: Vector3, b: Vector3):
    return math.sqrt((a.x - b.x)**2 + (a.y - b.y)**2 + (a.z - b.z)**2)

def main(xr: SyncXR, params: dict):
    
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
        
    

    eyepos = xr.eye().position

    elements = []

    NUM_OBJECTS = 5

    RADIUS = 0.2

    for i in range(NUM_OBJECTS):
        angle = i * (2 * math.pi / NUM_OBJECTS) + (math.pi / 2)
        x = math.cos(angle) * RADIUS
        y = math.sin(angle) * RADIUS
        elements.append(Element(
            key = f'button_{i}',
            transform = Transform(
                position = Vector3.from_xyz(eyepos.x + x, eyepos.y + y, eyepos.z),
                scale = Vector3.one() * 0.05,
            ),
            asset = DefaultAssets.CUBE
        ))

    wrench_element = Element(
        key = f'wrench',
        transform = Transform(
            position = Vector3.from_xyz(eyepos.x, eyepos.y - .2, eyepos.z - 0.4),
            scale = Vector3.one() * 0.01,
        ),
        asset = WRENCH_ASSET
    )

    elements.append(wrench_element)
    
    xr.update(wrench_element)
    wrench_element.asset = None
    
    panel = Element(
        key = 'panel',
        transform = Transform(
            position = xr.eye().position + Vector3.from_xyz(eyepos.x, eyepos.y - 1.15, eyepos.z + 0.5), # +y is up, -y is down, +z is away from user (forward)
            scale = Vector3.one() * 0.6,
        ),
        # eye = Pose(
        #     position = xr.eye().position + Vector3.from_xyz(eyepos.x, eyepos.y - 0.9, eyepos.z),
        # ),
        asset = ImageAsset.from_obj(obj = Image.open('assets/bike-seat-diagram.jpg')),
        # distance = 0.5
    )

    faux_seat = Element(
        key = 'seat',
        transform = Transform(
            position = Vector3.zero(),
            scale = Vector3.one() * 0.15,
        ),
        asset = DefaultAssets.CUBE,
        color = WHITE
    )
    elements.append(faux_seat)
    
    xr.update(panel)

    # l: bool = False
    # r: bool = False

    held: bool = False
    frame_touched: bool = False
    seat_held: bool = False

    stream = xr.sense(hands=True)
    for frame in stream:
        
        held = ui_drag(wrench_element, frame, .1, held) 

        # if (not frame_touched) and frame['hands'].right and distance(frame['hands'].right[INDEX_TIP].position, panel.eye.position) < .3:       
        if (not frame_touched) and ui_button(panel, frame, .3):       
            print("hi")
            frame_touched = True
            faux_seat.transform.position = frame['hands'].right[INDEX_TIP].position
            faux_seat.color = WHITE
        
        if frame_touched:
            seat_held = ui_drag(faux_seat, frame, .1, seat_held)
        
        # TBD: We will implement the logic to make the menu wheel appear/dissape
        for button in elements:
            # res: bool = check_button(button, frame)
        


            # hands: Hands = frame['hands']
            # if (not r and hands.right and pinch(hands.right)):
            #     button.transform.scale += Vector3.one()
            #     print("increasing")
            #     r = True
            # elif hands.right and not pinch(hands.right):
            #     r = False
            
            # if (not l and hands.left and pinch(hands.left)):
            #     button.transform.scale -= Vector3.one()
            #     print("decreasing")
            #     l = True
            # elif hands.left and not pinch(hands.left):
            #     l = False

            # xr.update(button)
            xr.update(wrench_element)

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
