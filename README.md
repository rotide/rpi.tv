# rpi.tv


<b>What is rpi.tv?</b>
<br>
> After "cutting the cord" I found myself with a basic want which pay-for streaming services seemed fail at providing. That want is for a simple way to load up a queue of videos and have them play randomly on my TV. I wanted a simple way to "channel surf" without having to choose which particular video to play.<br><br>
rpi.tv is the backend system which is meant to control one or more raspberry pi devices running the rpi.tv-endpoint software.

<b>Technology</b>
<br>
> This project is written in Python and heavily utilizes the Flask micro-framework. While other technologies may have been better suited, I honestly just wanted to learn Flask and Python is my go-to. For better or worse, Python is my hammer and everything just tends to be a nail.<br><br>
To facilitate communication between rpi.tv backend and the rpi.tv endpoints, this project utilizes simple HTTP REST API calls. This backed hosts the API while the endpoint gathers from and sends updates to it.
