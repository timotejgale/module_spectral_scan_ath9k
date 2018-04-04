WiSHFUL Spectral Scan USRP Agent Module
============================

This is a prototypic implementation of a wireless agent providing the Unified
Programming Interfaces (UPIs) of the Wishful software platform for
radio and network control.

## Notes

Please note that before using this module the following UPIs must be defined: radio.scand_start, radio.scand_stop, radio.scand_reconf, radio.scand_read. IP address on server interfaces that are connected to USRPs must also be set.

This module is based on *wishful_module_spectral_scan_ath9k*.

## Acknowledgement

The research leading to these results has received funding from the European
Horizon 2020 Programme under grant agreement n645274 (WiSHFUL project).
