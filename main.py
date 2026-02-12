from xarp.express import SyncXR
from xarp.server import run, show_qrcode_link
from xarp.entities import Element, ImageAsset, GLBAsset, DefaultAssets
from xarp.spatial import Transform, Vector3, Pose
from xarp.gestures import INDEX_TIP, pinch
from xarp.spatial import Quaternion
from xarp.data_models import Hands
from PIL import Image
from dotenv import load_dotenv
import math

def distance(a: Vector3, b: Vector3):
    return math.sqrt((a.x - b.x)**2 + (a.y - b.y)**2 + (a.z - b.z)**2)

def main(xr: SyncXR, params: dict):
    
    #import GLB assets
    HEART_ASSET = GLBAsset()
    with open("assets/heart.glb", "rb") as f:
        HEART_ASSET.raw = f.read()
    
    SEAT_ASSET = GLBAsset()
    with open("assets/wrench.glb", "rb") as f:
        SEAT_ASSET.raw = f.read()
        
    # SEAT_ASSET_2 = GLBAsset()
    # with open("assets/bike_seat_2.glb", "rb") as f:
    #     SEAT_ASSET_2.raw = f.read()
        
    SEAT_ASSET_3 = GLBAsset()
    with open("assets/bike_seat_3.glb", "rb") as f:
        SEAT_ASSET_3.raw = f.read()
        
    

    eyepos = xr.eye().position

    buttons = []
    # for i in range(5):
    #     buttons.append(Element(
    #         key = f'button{i}',
    #         transform = Transform(
    #             position = Vector3.from_xyz(eyepos.x + (i * 0.1), eyepos.y, eyepos.z),
    #             scale = (Vector3.one() * 0.05) if i > 0 else Vector3.from_xyz(1, -1, 1)*0.05,
    #         ),
    #         asset = HEART_ASSET if i == 0 else SEAT_ASSET if i == 1 else DefaultAssets.CUBE
    #     ))
    buttons.append(Element(
        key = f'seat',
        transform = Transform(
            position = Vector3.from_xyz(eyepos.x, eyepos.y, eyepos.z),
            scale = Vector3.one(), #(scale is a member of transform)
        ),
        asset = HEART_ASSET,
    ))

    xr.update(buttons[0])
    buttons[0].asset = None

    l: bool = False
    r: bool = False

    stream = xr.sense(hands=True)
    for frame in stream:
        for button in buttons:
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

            xr.update(button)

    stream.close()

# doesn't seem to work?
# def element_update(xr: SyncXR, element: Element): #update element asset such that it is only fetched once
#     # if not element.asset == None:
#     #     element.asset = None
#     xr.update(element)

# Return true if an element is pinched by the right hand.
def ui_button(button: Element, frame: dict[str, Any]) -> bool:
    WHITE = (1,1,1,1)
    RED = (1,0,0,1)
    hands: Hands = frame['hands']
    if (not hands.right):
        button.color = WHITE
        return False

    handpos = hands.right[INDEX_TIP].position
    if distance(handpos, button.transform.position) < .1:
        button.color = RED
        if pinch(hands.right):
            return True
    else:
        button.color = WHITE
        return False

# Allow element to be dragged around by right hand.
def ui_draggable(ui: Element, frame: dict[str, Any]):
    pass

if __name__ == "__main__":
    show_qrcode_link()
    run(main)
