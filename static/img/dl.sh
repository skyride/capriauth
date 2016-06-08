#!/bin/bash

for i in `seq 1 8`; do
	wget "http://zkillboard.com/img/panel/${i}h.png"
	wget "http://zkillboard.com/img/panel/${i}m.png"
	wget "http://zkillboard.com/img/panel/${i}l.png"
	wget "http://zkillboard.com/img/panel/${i}r.png"
	wget "http://zkillboard.com/img/panel/${i}s.png"
done
