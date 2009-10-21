# This is a basic VCL configuration file for varnish.  See the vcl(7)
# man page for details on VCL syntax and semantics.

backend backend_0 {
	.host = "localhost";
	.port = "8080";
	.first_byte_timeout = 20s;

	.probe = {
		.url = "/probe";
		.timeout = 400 ms;
		.interval = 2s;
		.window = 4;
		.threshold = 3;
	}
}

sub vcl_recv {
	set req.backend = backend_0;

	if (req.backend.healthy) {
		set req.grace = 30s;
	} else {
		set req.grace = 15m;
	}

	if (req.request != "GET" &&
		req.request != "HEAD" &&
		req.request != "PUT" &&
		req.request != "POST" &&
		req.request != "TRACE" &&
		req.request != "OPTIONS" &&
		req.request != "DELETE") {
		/* Non-RFC2616 or CONNECT which is weird. */
		pipe;
	}

	if (req.request != "GET" && req.request != "HEAD") {
		/* We only deal with GET and HEAD by default */
		pass;
	}

	if (req.http.Accept-Encoding) {
		if (req.http.Accept-Encoding ~ "gzip") {
			set req.http.Accept-Encoding = "gzip";
		} elsif (req.http.Accept-Encoding ~ "deflate") {
			set req.http.Accept-Encoding = "deflate";
		} else {
			# unkown algorithm
			remove req.http.Accept-Encoding;
		}
	}

	lookup;
}

sub vcl_pipe {
	# This is not necessary if you do not do any request rewriting.
	set req.http.connection = "close";
}

sub vcl_hit {
	if (!obj.cacheable) {
		pass;
	}
}

sub vcl_fetch {
	set obj.grace = 30s;
	if (!obj.cacheable) {
		pass;
	}
	if (obj.http.Set-Cookie) {
		pass;
	}
	if (obj.http.Cache-Control ~ "(private|no-cache|no-store)") {
		pass;
	}
	if (req.http.Authorization && !obj.http.Cache-Control ~ "public") {
		pass;
	}
}

sub vcl_deliver {
	# Remove some headers that are not necessary.
	remove resp.http.X-Varnish;
	remove resp.http.Via;

	# Remove caching headers as they take quite a many bytes.
	remove resp.http.Cache-Control;
	remove resp.http.Expires;
	remove resp.http.Vary;
	remove resp.http.Age;
}
