Tutorial 1 - Fahrenheit to Celcius
==================================

In this tutorial we will make your application do something interesting.

Add code to your project
------------------------

In this step we assume that you followed the :doc:`previous tutorial <tutorial-0>`.
Put the following code into ``helloworld\app.py``, replacing the old code:

.. code-block:: python

  import toga


  class Converter(toga.App):
      def calculate(self, widget):
          try:
              self.c_input.value = (float(self.f_input.value) - 32.0) * 5.0 / 9.0
          except Exception:
              self.c_input.value = '???'

      def startup(self):
          self.main_window = toga.MainWindow(self.name)
          self.main_window.app = self

          # Tutorial 1
          c_box = toga.Box()
          f_box = toga.Box()
          box = toga.Box()

          self.c_input = toga.TextInput(readonly=True)
          self.f_input = toga.TextInput()

          c_label = toga.Label('Celcius', alignment=toga.LEFT_ALIGNED)
          f_label = toga.Label('Fahrenheit', alignment=toga.LEFT_ALIGNED)
          join_label = toga.Label('is equivalent to', alignment=toga.RIGHT_ALIGNED)

          button = toga.Button('Calculate', on_press=self.calculate)

          f_box.add(self.f_input)
          f_box.add(f_label)

          c_box.add(join_label)
          c_box.add(self.c_input)
          c_box.add(c_label)

          box.add(f_box)
          box.add(c_box)
          box.add(button)

          box.style.set(flex_direction='column', padding_top=10)
          f_box.style.set(flex_direction='row', margin=5)
          c_box.style.set(flex_direction='row', margin=5)

          self.c_input.style.set(flex=1)
          self.f_input.style.set(flex=1, margin_left=160)
          c_label.style.set(width=100, margin_left=10)
          f_label.style.set(width=100, margin_left=10)
          join_label.style.set(width=150, margin_right=10)
          button.style.set(margin=15)

          self.main_window.content = box
          self.main_window.show()


  def main():
      return Converter('Converter', 'org.pybee.converter')


Build and run the app
---------------------

Now you can invoke briefcase again:

.. code-block:: bash

  $ python setup.py ios -s

replacing ``ios`` with your platform of choice. You will be asked if you want
to replace the existing ``ios`` (or whatever platform you choose) directory; answer
``y``, and a new project will be generated and started.

You should see something that looks a bit like this:

.. image:: screenshots/tutorial-1-ios.png

Use the *same code*, but for the web
------------------------------------

Now, we're going to deploy the same code, but as a single page web
application. Make sure you have the Django dependencies installed (see
:doc:`/background/getting-started`), and run the following:

.. code-block:: bash

  $ python setup.py django -s

This will gather all the Javascript dependencies, create an initial database, start a Django runserver, and launch a browser. You should see the same application running in your browser:

.. image:: screenshots/tutorial-1-django.png

.. note::

   If you get a "Server could not be contacted" error, it's possible your web browser
   started faster than the server; reload the page, and you should see the app.

