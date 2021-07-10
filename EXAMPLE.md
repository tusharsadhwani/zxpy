# A larger, practical example

Suppose you want to find all the GitHub repositories that you (or someone else)
has contributed to, other than their own.

Luckily you can simply query the GitHub Public API to find this out. Reading its
[documentation][1], you can find out about its [`/search/issues` endpoint][2].

Running a curl script like so, would get you the data:

```console
$ curl -s 'https://api.github.com/search/issues?q=author:tusharsadhwani+is:pull-request+is:merged&per_page=100'
"total_count": 74,
  "incomplete_results": false,
  "items": [
    {
      "url": "https://api.github.com/repos/tusharsadhwani/zxpy/issues/16",
      "repository_url": "https://api.github.com/repos/tusharsadhwani/zxpy",
      ...
```

Now you can pipe this data through a JSON parser like `jq` to filter out the urls within the `items` array:

```console
$ curl -s 'https://api.github.com/search/issues?q=author:tusharsadhwani+is:pull-request+is:merged&per_page=100' \
  | jq '.items[].repository_url'
"https://api.github.com/repos/tusharsadhwani/zxpy"
"https://api.github.com/repos/tusharsadhwani/zxpy"
"https://api.github.com/repos/tusharsadhwani/piston_bot"
...
```

... and now, all we have to do is:

- use `sed` to extract the org and repo name from the url,
- use `grep` with `-v` to filter out the their own repositories,
- use `sort` with the `-u` flag to get a unique set of org/repo pairs,
- and use `wc -l` to count the number of repositories.

The completed bash command looks something like this:

```console
$ curl -s 'https://api.github.com/search/issues?q=author:tusharsadhwani+is:pull-request+is:merged&per_page=100' \
  | jq '.items[].repository_url' \
  | sed -E 's/.+\/(.+?)\/(.+?)\"$/\1:\2/' \
  | grep -v 'tusharsadhwani' \
  | sort -u \
  | wc -l
20
```

Now if I'm being honest, I'm not someone who would look up and willingly read the man pages of 5 of these specialized linux programs, when I know that Python has most of this functionality baked into it, which is simpler and (arguably) easier to read and maintain!

So let's use zxpy for this instead. Since I personally don't like `urllib`, we're going to use `curl` directly instead:

```python
import json

# this will hold unique tuples of (org_name, repo_name)
repos = set()

response = ~(
    "curl -s 'https://api.github.com/search/issues"
    "?q=author:tusharsadhwani"
    "+is:pull-request"
    "+is:merged"
    "&per_page=100'"
)
data = json.loads(response)
pull_requests = data['items']

for pr in pull_requests:
    repo_url = pr['repository_url']
    *_, org_name, repository = repo_url.split('/')

    if org_name != 'tusharsadhwani':
        repos.add((org_name, repository))

print(len(repos))
```

Output:

```console
$ zxpy repo_count.py
20
```

---

Let's say we wanted to clone each of those repositories instead:

- Using bash:

  ```console
  $ curl -s 'https://api.github.com/search/issues?q=author:tusharsadhwani+is:pull-request+is:merged&per_page=100' \
    | jq '.items[].repository_url' \
    | sed -E 's/.+\/(.+?)\/(.+?)\"$/https:\/\/github.com\/\1\/\2/' \
    | grep -v 'tusharsadhwani' \
    | sort -u \
    | xargs -n1 git clone
  Cloning into 'astpretty'...
  remote: Enumerating objects: 374, done.
  remote: Counting objects: 100% (93/93), done.
  remote: Compressing objects: 100% (89/89), done.
  remote: Total 374 (delta 44), reused 8 (delta 4), pack-reused 281
  Receiving objects: 100% (374/374), 84.60 KiB | 288.00 KiB/s, done.
  Resolving deltas: 100% (203/203), done.
  Cloning into 'air'...
  ...
  ```

- Using zxpy:

  ```python
  import json

  # this will hold unique tuples of (org_name, repo_name)
  repos = set()

  response = ~(
      "curl -s 'https://api.github.com/search/issues"
      "?q=author:tusharsadhwani"
      "+is:pull-request"
      "+is:merged"
      "&per_page=100'"
  )
  data = json.loads(response)
  pull_requests = data['items']
  for pr in pull_requests:
      repo_url = pr['repository_url']
      *_, org_name, repository = repo_url.split('/')

      if org_name != 'tusharsadhwani':
          repos.add((org_name, repository))

  for org, repo in repos:
      print(f'cloning {repo} from {org}...')
      ~f"git clone https://github.com/{org}/{repo}"

  print('Done!')
  ```

  Output:

  ```console
  $ zxpy clone_repos.py
  cloning astpretty from asottile...
  cloning cpython from python...
  ...
  Done!
  ```

While in the bash example we had to modify the regex used with `sed` quite a bit, and also use `xargs`, in the zxpy script we just had to add a simple for loop at the end.

[1]: https://docs.github.com/en/rest/reference
[2]: https://docs.github.com/en/rest/reference/issues
