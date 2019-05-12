# Odrive Web Interface

A Pi based webserver that controls the ODrive Brushless motor controller.

You'll need to add a JQuery.js in the static folder.

At the moment this only supports the first motor of the first ODrive found.

Web Commands are in this form:

  class='button' onclick="socket.emit('do_job',{'scycle': '2048/0.02'});"> 1/4 Rev 0.02

Which is effectively 'Go to position 2048 in 0.02 seconds'  This is about as fast as the motor I'm testing will go.

For much slower moves use:

  class='button' onclick="socket.emit('do_job',{'trajectory_to': '5000/2'});"> Move to 5000/2

Which uses the move_to_pos trajectory method, this means go to position 5000 at a rate of 2 cycles per second - which is very slow.
The move_to_pos method is asynchronous and may need to be cancelled using:

   class='button' onclick="socket.emit('do_job',{'cancel_trajectory': 'NOP'});"> Cancel Move

   
