import pytest

TEST_TITLE = "ANDROID_HOME and ANDROID_SDK_ROOT are inconsistent"
TEST_MESSAGE = """
    The ANDROID_HOME and ANDROID_SDK_ROOT environment variables
    are set to different paths:

      ANDROID_HOME:     /briefcase/tests/console/Console/test_warning_banner.py
      ANDROID_SDK_ROOT: /home/anton/briefcase/tests/console/Console/test_warning_banner.py

    Briefcase will ignore ANDROID_SDK_ROOT and only use the path
    specified by ANDROID_HOME.

    You should update your environment configuration to either
    not set ANDROID_SDK_ROOT, or set both environment variables
    to the same path.
"""  # noqa: E501


@pytest.mark.parametrize(
    ("title", "message", "width", "expected"),
    [
        # Default width (80) with title and message
        pytest.param(
            TEST_TITLE,
            TEST_MESSAGE,
            80,
            """*************************************************************************
            ******* **        WARNING: ANDROID_HOME and ANDROID_SDK_ROOT are
            inconsistent         ** ****************************************************
            ****************************

              The ANDROID_HOME and ANDROID_SDK_ROOT environment variables are set to
              different paths:

                ANDROID_HOME:     /briefcase/tests/console/Console/test_warning_banner.py
                ANDROID_SDK_ROOT: /home/anton/briefcase/tests/console/Console/test_warning_banner.py

              Briefcase will ignore ANDROID_SDK_ROOT and only use the path specified by
              ANDROID_HOME.

              You should update your environment configuration to either not set
              ANDROID_SDK_ROOT, or set both environment variables to the same path.

            ********************************************************************************
            """,
            id="80-char",
        ),
        # Wrap to 60 chars
        pytest.param(
            TEST_TITLE,
            TEST_MESSAGE,
            60,
            """************************************************************ **
            WARNING: ANDROID_HOME and ANDROID_SDK_ROOT are     ** **
            inconsistent                      **
            ************************************************************

              The ANDROID_HOME and ANDROID_SDK_ROOT environment
              variables are set to different paths:

                ANDROID_HOME:     /briefcase/tests/console/Console/test_warning_banner.py
                ANDROID_SDK_ROOT: /home/anton/briefcase/tests/console/Console/test_warning_banner.py

              Briefcase will ignore ANDROID_SDK_ROOT and only use the
              path specified by ANDROID_HOME.

              You should update your environment configuration to
              either not set ANDROID_SDK_ROOT, or set both environment
              variables to the same path.

            ************************************************************
            """,
            id="60-char",
        ),
        # Wrap to 120 chars
        pytest.param(
            TEST_TITLE,
            TEST_MESSAGE,
            120,
            """*************************************************************************
            *********************************************** **
            WARNING: ANDROID_HOME and ANDROID_SDK_ROOT are inconsistent
            ** *************************************************************************
            ***********************************************

              The ANDROID_HOME and ANDROID_SDK_ROOT environment variables are set to different paths:

                ANDROID_HOME:     /briefcase/tests/console/Console/test_warning_banner.py
                ANDROID_SDK_ROOT: /home/anton/briefcase/tests/console/Console/test_warning_banner.py

              Briefcase will ignore ANDROID_SDK_ROOT and only use the path specified by ANDROID_HOME.

              You should update your environment configuration to either not set ANDROID_SDK_ROOT, or set both environment
              variables to the same path.

            ************************************************************************************************************************
            """,  # noqa: E501
            id="120-char",
        ),
        # Default width (80) without title
        pytest.param(
            None,
            TEST_MESSAGE,
            80,
            """*************************************************************************
            *******

              The ANDROID_HOME and ANDROID_SDK_ROOT environment variables are set to
              different paths:

                ANDROID_HOME:     /briefcase/tests/console/Console/test_warning_banner.py
                ANDROID_SDK_ROOT: /home/anton/briefcase/tests/console/Console/test_warning_banner.py

              Briefcase will ignore ANDROID_SDK_ROOT and only use the path specified by
              ANDROID_HOME.

              You should update your environment configuration to either not set
              ANDROID_SDK_ROOT, or set both environment variables to the same path.

            ********************************************************************************
            """,
            id="no-title",
        ),
        pytest.param(
            TEST_TITLE,
            None,
            80,
            """*************************************************************************
            ******* **        WARNING: ANDROID_HOME and ANDROID_SDK_ROOT are
            inconsistent         ** ****************************************************
            ****************************""",
            id="title-only",
        ),
        # Message and title lengths equal to box width
        pytest.param(
            "Length of ............. width",
            "Length of message is equal to box width.",
            44,
            """******************************************** ** WARNING: Length of
            ............. width ** ********************************************

            Length of message is equal to box width.

            ********************************************
            """,
            id="exact-width",
        ),
        pytest.param(
            "Length+ of ............. width",
            "Length+ of message is equal to box width.",
            44,
            """******************************************** **   WARNING: Length+ of
            .............    ** **                 width                  **
            ********************************************

            Length+ of message is equal to box width.

            ********************************************
            """,
            id="1-char-wrap",
        ),
        pytest.param(
            None,
            """Start text with literal.

            More text

             - bullet point
             - other bullet point


            Text after two new lines.

              A single literal.

            Text following a literal, followed by a blank line.
            """,
            40,
            """
****************************************

    Start text with literal

  More text

   - bullet point
   - other bullet point


  Text after two new lines.

    A single literal.

  Text following a literal, followed
  by a blank line.

****************************************
""",
            id="line-breaks",
        ),
    ],
)
def test_warning_banner(console, title, message, width, expected, capsys):
    """Test warning_banner with various inputs."""
    # call the function
    console.warning_banner(title=title, message=message, width=width)
    # capture console output
    output = capsys.readouterr().out

    assert expected == output
