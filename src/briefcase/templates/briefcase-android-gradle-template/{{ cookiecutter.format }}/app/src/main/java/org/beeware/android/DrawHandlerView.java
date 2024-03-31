package org.beeware.android;

public class DrawHandlerView extends android.view.View {
    private IDrawHandler drawHandler = null;

    public DrawHandlerView(android.content.Context context) {
        super(context);
    }

    public void setDrawHandler(IDrawHandler drawHandler) {
        this.drawHandler = drawHandler;
    }

    public void onDraw(android.graphics.Canvas canvas) {
        super.onDraw(canvas);
        drawHandler.handleDraw(canvas);
    }
}
