See Errors on iOS
=========================

If you have a beeware iOS project that has a crash, it can be difficult to see
the stacktrace. Here's how to do it -

1. Build your iOS project. You don't have to start it.

2. Open that iOS project in Xcode.  Click the Run button (looks like an arrow)
   and wait for the simulator to open. Cause the app to crash.

3. Your stack trace ought to appear in the 'debugger area' at the bottom of the
   screen. If you can't see that area, you may have to activate it with
   ``View`` > ``Debug Area`` > ``Show Debug Area``

 .. image:: PyStackTraceOnXCode.png
