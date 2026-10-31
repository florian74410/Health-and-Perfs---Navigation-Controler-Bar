"""Native desktop commands must not load the frozen application's Qt/GLib libraries."""
import os


def native_env():
    env = os.environ.copy()
    for key in ('LD_LIBRARY_PATH', 'DYLD_LIBRARY_PATH'):
        if key+'_ORIG' in env:
            original=env[key+'_ORIG']
            # Older updaters could pass their own embedded libraries to the new runtime.
            env[key] = os.pathsep.join(p for p in original.split(os.pathsep)
                                      if not p.rstrip('/').endswith('/HealthPerfsBar/_internal'))
        else:
            env.pop(key, None)
    for key in ('QT_PLUGIN_PATH', 'QT_QPA_PLATFORM_PLUGIN_PATH', 'PYTHONHOME'):
        env.pop(key, None)
    return env
