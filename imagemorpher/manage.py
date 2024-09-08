#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    if os.environ.get('MORPH_DEBUG') == 'true':
        debug_port = os.environ.get('DEBUG_PORT', 5680)
        import debugpy
        debugpy.listen(("0.0.0.0", int(debug_port)))
        print(f"⏳ Waiting for debugger to attach on port {debug_port}...")
    else:
        print("manage.py: Debugging disabled")

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'imagemorpher.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        )
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
