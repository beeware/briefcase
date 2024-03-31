package org.beeware.android;

import android.content.Intent;
import android.content.res.Configuration;
import android.view.Menu;
import android.view.MenuItem;

public interface IPythonApp {
    void onCreate();
    void onResume();
    void onStart();
    void onActivityResult(int requestCode, int resultCode, Intent data);
    void onConfigurationChanged(Configuration newConfig);
    boolean onOptionsItemSelected(MenuItem menuitem);
    boolean onPrepareOptionsMenu(Menu menu);
    // There's no need to add any more methods to this interface, as the Python
    // call mechanism no longer uses it.
}
