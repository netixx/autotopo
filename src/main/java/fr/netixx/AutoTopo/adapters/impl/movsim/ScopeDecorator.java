package fr.netixx.AutoTopo.adapters.impl.movsim;

import fr.netixx.AutoTopo.Settings;

import java.awt.Color;
import java.util.Hashtable;
import java.util.Random;

public class ScopeDecorator {

	private static final float MAX_HUE = 360f;
	private static final float HUE_STEP = Settings.getFloat(Settings.DECORATION_SCOPE_HUE_STEP)/MAX_HUE;

	private static Hashtable<Integer, Integer> idToRgb = new Hashtable<>();
	private static float hue = 0f;
	private static Random rand = new Random();

	public static int idToRgb(int id) {
		if (!idToRgb.containsKey(id)) {
			idToRgb.put(id, newColor());
		}

		return idToRgb.get(id);
	}



	private static int newColor() {
		// restart if hue outside of range
		hue += HUE_STEP;

//		return Color.getHSBColor(hue++, 90 + rand.nextFloat() * 10, 50 + rand.nextFloat() * 10).getRGB();
		return Color.getHSBColor(hue, 1, 1).getRGB();
	}

}
