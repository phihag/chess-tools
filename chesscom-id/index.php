<?php

// Alternative: https://www.chess.com/callback/user/daily/games?limit=1&userId=214563005

$id = isset($_GET['id']) ? $_GET['id'] : '';
if ($id) {
	$opts = [
	    'https' => [
	        'method' => 'GET',
	        'header' => 'User-Agent: chess-tools (phihag@phihag.de)\r\n',
	    ],
	];
	$context = \stream_context_create($opts);
	$error = null;

	$is_uuid = \str_contains($id, '-');
	$url = 'https://www.chess.com/callback/user/id-to-data?ids[]=' . \urlencode($id);
	$response_json = @\file_get_contents($url, false, $context);
	if ($response_json === false) {
		$error = 'Failed to fetch ' . $url . ' (wrong ID?)';
	} else {
		$response_data = \json_decode($response_json, true);
        if ($response_data === false) {
			$error = 'Download failed.';
		} else {
			$values = \array_values($response_data);
			$username = $values[0]['username'];
		}
	}
}

?>
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Look up chess.com username by ID</title>
<style type="text/css">
html, body {font-family: sans-serif;}
body {text-align: center;}
h1 {font-size: 40px;}
input, button {
	padding: 15px 15px;
	font-size: 30px;
}
#result {font-size: 40px;}
#error {font-size: 30px; color: red;}
</style>
</head>
<body>

<h1>Look up chess.com user by ID</h1>
<form method="get">
<input pattern="^[0-9]+|[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$" required="required" title="Must be a number or UUID" placeholder="numeric ID or UUID" name="id" value="" autofocus="autofocus" size="30">
<button type="submit" style="margin-left: 10px">Look up username</button>
</form>

<?php
if ($id) {
	if ($error) {
		echo '<p id="error">Error while fetching username of <code>' . \htmlspecialchars($id) . '</code>: ';
		echo \htmlspecialchars($error) . ' Contact R_Doofus.';
	} else {
		echo (
			'<p id="result"><code>' . \htmlspecialchars($id) . '</code> is user ' .
			'<a href="https://www.chess.com/member/' . \htmlspecialchars($username) . '">' .
			htmlspecialchars($username) . '</a></p>');
	}
}
?>
</body>
</html>