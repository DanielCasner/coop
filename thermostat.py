#!/usr/bin/env python3
"""
Chicken coop temperature controller module.
"""
__author__ = "Daniel Casner"

class Thermostat(object):
    "Basic class for managing temperature"
    
    def __init__(self, heater, cooler, k_p, k_i, k_d, i_max):
        """Sets up the thermostat
        heater and cooler are objects that have set and clamp methods specifying their outputs and max outputs in range 
        [0.0 .. 1.0]
        k_p, k_i and k_d are terms PID controller gains.
        i_max = maximum integral term
        """
        self.heater = heater
        self.cooler = cooler
        self.kp = k_p
        self.ki = k_i
        self.kd = k_d
        self.i_max = i_max
        self._last_sample = None
        self._heat_target = None
        self._cool_target = None
        self._heat_integral = 0
        self._cool_integral = 0
    
    def __del__(self):
        if self.cooler is not None:
            self.cooler.set(0)
        if self.heater is not None:
            self.heater.set(0)
    
    def heat_target():
        doc = "The heating target for the thermostat."
        def fget(self):
            return self._heat_target
        def fset(self, value):
            self._heat_target = value
            if self._last_sample is not None: # If we have some data, adjust the output right away
                self.send(self._last_sample)
        def fdel(self):
            self._heat_target = None
        return locals()
    heat_target = property(**heat_target())
    
    def cool_target():
        doc = "The cooling target of the thermostat."
        def fget(self):
            return self._cool_target
        def fset(self, value):
            self._cool_target = value
            if self._last_sample is not None: # If we have some data, adjust the output right away
                self.send(self._last_sample)
        def fdel(self):
            del self._cool_target
        return locals()
    cool_target = property(**cool_target())

    def clamp_heater(self, clamp):
        "Clamps the heaters maximum output"
        self.heater.clamp(clamp)

    def clamp_cooler(self, clamp):
        "Clamps the coolers maximum output"
        self.cooler.clamp(clamp)

    def send(self, temperature):
        "Send a temperature sample to the thermostat and update its outputs"
        if self.heater is not None and self._heat_target is not None:
            e = temperature - self._heat_target
            d = temperature - self._last_sample
            self._heat_integral += e
            if abs(elf._heat_integral) > self.i_max:
                self._heat_integral = self.i_max if self._heat_integral > 0 else -self.i_max
            c = self.kp * e + self.ki * self._heat_integral + self.kd * d
            if c < 0.0:
                c = 0.0
            elif c > 1.0:
                c = 1.0
            self.heater.set(c)
        if self.cooler is not None and self._cool_target is not None:
            e = temperature - self._cool_target
            d = temperature - self._last_sample
            self._cool_integral += e
            if abs(self._cool_integral) > self.i_max:
                self._cool_integral = self.i_max if self._cool_integral > 0 else -self.i_max
            c = (self.kp * e + self.ki * self._cool_integral + self.kd * d) * -1.0 # Negative 1 because the cooler command is inverted
            if c > 0.0:
                c = 0.0
            elif c < -1.0:
                c = -1.0
            self.cooler.set(c)
        self._last_sample = temperature
