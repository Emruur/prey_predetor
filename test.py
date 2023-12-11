from pp_env import pp_env
from random import randint
from PIL import Image
import os

env = pp_env(render_mode="human", max_steps= 100)
observations, infos = env.reset()

frame_list= []
while env.agents:
    # this is where you would insert your policy
    actions = {agent: randint(0,6) for agent in env.agents}
    frame= env.render()
    frame_list.append(Image.fromarray(frame))
    observations, rewards, terminations, truncations, infos = env.step(actions)

dir_path = "gif"  # This will create a 'gif' directory in the same directory as your script
if not os.path.exists(dir_path):
    os.makedirs(dir_path)

output_path = os.path.join(dir_path, 'out111.gif')
frame_list[0].save(output_path,
                           save_all=True, append_images=frame_list[1:], duration=1, loop=0)
env.close()