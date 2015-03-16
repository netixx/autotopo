package fr.netixx.AutoTopo.helpers;

import java.io.InputStream;
import java.net.URI;
import java.net.URISyntaxException;

public class ResourcesHelper {

	public static InputStream getResourceStream(final String resource) {
		return getClassLoader().getResourceAsStream(resource);
	}

	public static URI getResource(final String resource) throws URISyntaxException {
		return getClassLoader().getResource(resource).toURI();
	}

	private static ClassLoader getClassLoader() {
		return Thread.currentThread().getContextClassLoader();
	}
}
