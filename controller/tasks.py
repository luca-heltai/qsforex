from __future__ import absolute_import

from qsforex.controller.app import app


@app.task(name='qsforex.controller.tasks.ProcessTick')
def ProcessTick(tick):
    print tick
