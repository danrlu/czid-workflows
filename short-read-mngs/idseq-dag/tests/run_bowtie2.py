import unittest

import os
import subprocess
import time

from .idseq_step_setup import IdseqStepSetup
from idseq_dag.engine.pipeline_flow import PipelineFlow
from idseq_dag.steps.run_bowtie2 import PipelineStepRunBowtie2

class RunBowtie2Test(unittest.TestCase):

    def test_step_paired(self):
        runstep = IdseqStepSetup.getStepObject(PipelineStepRunBowtie2, "run_bowtie2", paired=True)
        runstep.start()
        runstep.wait_until_finished()
        # Check results
        # Clean up the folder

    def test_step_single(self):
        runstep = IdseqStepSetup.getStepObject(PipelineStepRunBowtie2, "run_bowtie2", paired=False)
        runstep.start()
        runstep.wait_until_finished()
        # Check results
        # Clean up the folder



