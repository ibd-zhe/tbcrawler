
def alphanum(text):
    return ''.join(j for j in text if j.isalnum())

class Cache:
    def __init__(self, fget):
        self._attr_name = fget.__name__
        self.fget = fget

    def __get__(self, instance, owner):
        attr = self.fget(instance)
        setattr(instance, self._attr_name, attr)
        return attr



