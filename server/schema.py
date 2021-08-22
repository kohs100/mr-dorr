PATTERN_SID = r'^[A-Fa-f0-9]{8}$'


class Schema():
    ep_refrig_post = {
        "title": "heartbeat",
        "type": "object",
        "properties": {
            "opened": {
                "type": "boolean"
            },
            "status": {
                "type": "object",
                "patternProperties": {
                    PATTERN_SID: {
                        "type": "object",
                        "properties": {
                            "numslot": {
                                "type": "integer",
                                "minimum": 1
                            },
                            "mainslot": {
                                "type": "integer",
                                "minimum": 0,
                            },
                            "status": {
                                "type": "array",
                                "items": {
                                    "type": ["string", "null"]
                                }
                            }
                        }
                    }
                },
                "additionalProperties": False
            }
        },
        "required": ["opened", "status"]
    }

    ep_stat_update = {
        "type": "object",
        "properties": {
            "status": {
                "type": "object",
                "patternProperties": {
                    PATTERN_SID: {
                        "title": "mainslot",
                        "type": "integer",
                        "minimum": 0,
                    }
                },
                "additionalProperties": False
            }
        },
        "required": ["status"]
    }

    ep_stat_create = {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "minLength": 1
            }
        },
        "required": ["name"]
    }

    ep_db_create = {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "minLength": 1
            }
        },
        "required": ["name"]
    }
