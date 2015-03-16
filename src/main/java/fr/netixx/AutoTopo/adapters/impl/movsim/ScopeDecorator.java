package fr.netixx.AutoTopo.adapters.impl.movsim;

import java.awt.Color;
import java.util.Hashtable;
import java.util.Random;

public class ScopeDecorator {

	private static final int MAX_HUE = 360;
	private static final int HUE_STEP = 23;

	private static Hashtable<Integer, Integer> idToRgb = new Hashtable<>();
	private static int hue = 0;
	private static Random rand = new Random();

	public static int idToRgb(int id) {
		if (!idToRgb.containsKey(id)) {
			int rgb = newColor();
			idToRgb.put(id, rgb);
		}

		return idToRgb.get(id);

	}



	private static int newColor() {
		// restart if hue outside of range
		hue = (hue + HUE_STEP) % MAX_HUE;
		return Color.getHSBColor(hue++, 90 + rand.nextFloat() * 10, 50 + rand.nextFloat() * 10).getRGB();
	}

}
