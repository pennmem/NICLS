.. sectnum::

#############
Network Protocol & Logged Events
#############

This is the network protocol document for NICLS.

.. contents:: **Table of Contents**
    :depth: 2

*************
Overview
*************

This is adapted from the protocol that was used by Ramulator to synchronize stimulation with task phases as well as extensions needed for additional functionality in NICLS.
Communication on the task side is handled by sending JSON strings over a tcp connection to, by default, 127.0.0.1 port 8889.

*************
Network Protocol
*************

This section contains the key and the messsages.

=============
Important Notes
=============

Important notes about the networking system.

* There is no timeout on return communication

=============
Key
=============

The key information for understanding the protocol below.

* Each mesasge has the message type (type), the timestamp (time), and the data (data)

=============
Required Messages
=============

These messages are required for NICLS to function 

* CONNECTED:
    * Message: {"type”: "CONNECTED”, data: {}, "time”: <float>}
    * Response: {"type”: "CONNECTED_OK”, "time”: <float>}

* CONFIGURE:
    * Message: {"type”: "CONFIGURE”, data: {}, "time”: <float>}
    * Response Ok: {"type”: "CONFIGURE_OK”, "data": <config dict>, "time”: <float>}
    * Response Error: {"type”: "ERROR_IN_CONFIGURATION”, "time”: <float>}
    * Response Error: {"type”: "ERROR_IN_CONFIG_FILE”, "time”: <float>}
    * Note: Configure is more 

* READY:
    * Message: {"type”: "READY”, "data”: {}, "time”: <float>}
    * Response: {"type”: "START”, "data”: {}, "time”: <float>}

* HEARTBEAT:
    * Message: {"type”: "HEARTBEAT”, "data”: {"count”: 27}, "time”: <float>}
    * Response: {"type”: "HEARTBEAT_OK”, "data”: {"count”: 27}, "time”: <float>}
    * Note: "data”: "count” increases with each heartbeat.  Should be sent once per second.

=============
Handled Messages
=============

These are messages that NICLS does something as a result of receiving them.

* CLASSIFIER_ON:
    * Message: {"type”: "CLASSIFIER_ON”, "data”: {}, "time”: <float>}
    * Response: None
    * Purpose: Starts classification

* CLASSIFIER_OFF:
    * Message: {"type”: "CLASSIFIER_OFF”, "data”: {}, "time”: <float>}
    * Response: None
    * Purpose: Stops classification

* ENCODING:
    * Message: {"type”: "ENCODING”, "data”: {"enable": <bool>}, "time”: <float>}
    * Response: None
    * Purpose: Marks an (word) encoding event. The classifier will use this for normalization

* READ_ONLY_STATE:
    * Message: {"type”: "READ_ONLY_STATE”, "data”: {"enable": <bool>}, "time”: <float>}
    * Response: None
    * Purpose: Marks the state as read only. Setting this value to "true" will reset the normalization stats. Any encoding events sent while this state is "true" will update the normalization stats. Setting this to false will allow the classifier to use the normalization stats.

=============
Send Only Messages
=============

These are messages sent from NICLS that aren't a response.

* CLASSIFIER_RESULT:
    * Message: {"type”: "CLASSIFIER_RESULT”, "data”: {"id":<int>, "result":<int>, "prob":<float>, "normalized":<string of bool>, "classifier duration":<float>}, "time”: <float>}
    * Response: None
    * Purpose: This is the result of a classification epoch

