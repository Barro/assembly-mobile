# This is a basic VCL configuration file for varnish.  See the vcl(7)
# man page for details on VCL syntax and semantics.

backend backend_0 {
        .host = "127.0.0.1";
        .port = "8080";
        .first_byte_timeout = 300s;

        .probe = {
                .url = "/probe";
                .timeout = 100 ms;
                .interval = 1s;
                .window = 4;
                .threshold = 3;
        }
}


acl purge {
    "localhost";
}

sub vcl_recv {
        set req.grace = 30s;
        set req.backend = backend_0;
	
	if (req.request == "PURGE") {
		if (!client.ip ~ purge) {
			error 405 "Not allowed.";
		}
		lookup;
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

	if (req.http.If-None-Match) {
		pass;
	}

	if (req.url ~ "createObject") {
		pass;
	}

	if (req.http.Accept-Encoding) {
		if (req.url ~ "\.(jpg|png|gif|gz|tgz|bz2|tbz|mp3|ogg)$") {
			# No point in compressing these
			remove req.http.Accept-Encoding;
		} elsif (req.http.Accept-Encoding ~ "gzip") {
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
	if (req.request == "PURGE") {
		purge_url(req.url);
		error 200 "Purged";
	}

	if (!obj.cacheable) {
		pass;
	}
}

sub vcl_miss {
	if (req.request == "PURGE") {
		error 404 "Not in cache";
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

