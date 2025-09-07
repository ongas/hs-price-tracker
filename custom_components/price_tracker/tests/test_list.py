import sys
import os
# Add both possible package roots to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../custom_components/price_tracker/custom_components/price_tracker')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../custom_components/price_tracker')))
from custom_components.price_tracker.utilities.list import Lu


def test_array_access():
    test = [
        {"entity": {"viewType": "ACCESS"}},
        {"entity": {"viewType": "ACCESS_TARGET"}},
    ]

    result = Lu.find(test, "entity.viewType", "ACCESS_TARGET")

    assert result == test[1]
