import json

from rockset import Client, Q

import config

client = Client(api_server='api.rs2.usw2.rockset.com',
                api_key=config.ROCKSET_API_KEY)

TOP_CONTRIBUTORS_QUERY = '''
WITH multi_contributor_repos as (
    SELECT gh.repo.name AS repo_name
    FROM "github" gh
    WHERE type = 'CommitCommentEvent'
    GROUP BY gh.repo.name
    HAVING COUNT(DISTINCT gh.actor.display_login) > 10
)
SELECT gh.actor.display_login Contributor, COUNT(gh.actor.display_login) AS Commits
FROM "github" gh
WHERE type = 'CommitCommentEvent' AND gh.repo.name IN (SELECT * FROM multi_contributor_repos)
GROUP BY gh.actor.display_login
ORDER BY Commits DESC
LIMIT 10;
'''

INDIVIDUAL_CONTRIBUTOR_RANK = '''
WITH
multi_contributor_repos as (
    SELECT gh.repo.name AS repo_name
    FROM "github" gh
    WHERE type = 'CommitCommentEvent'
    GROUP BY gh.repo.name
    HAVING COUNT(DISTINCT gh.actor.display_login) > 10
),
rank as (
    SELECT gh.actor.display_login Contributor, COUNT(gh.actor.display_login) AS Commits
    FROM "github" gh
    WHERE type = 'CommitCommentEvent' AND gh.repo.name IN (SELECT * FROM multi_contributor_repos)
    GROUP BY gh.actor.display_login
)
SELECT COUNT(*) as Rank
FROM rank
WHERE Commits >= (
    SELECT Commits FROM rank
    WHERE Contributor = '{}')
'''


def contributors(event, context):
    try:
        results = client.sql(Q(TOP_CONTRIBUTORS_QUERY)).results()
        return {"statusCode": 200, "body": json.dumps(results)}
    except Exception as e:
        print('Error finding top contributors {}'.format(e))
        return {"statusCode": 500, "body": json.dumps({'msg': 'Internal Error'})}


def rank(event, context):
    body = json.loads(event['body'])
    if not body or 'username' not in body:
        return {"statusCode": 200, "body": 'Pass username'}
    else:
        username = body['username']
        results = client.sql(Q(INDIVIDUAL_CONTRIBUTOR_RANK.format(username))).results()
        return {"statusCode": 200, "body": json.dumps(results)}


if __name__ == '__main__':
    top_contributors = contributors(None, None)
    print('Top Contributors {}'.format(json.dumps(top_contributors, indent=3)))

    username = 'discoursebot'
    body = {
        'username': username
    }

    print('Rank of {} is {}'.format(username, rank({'body': json.dumps(body)}, None)))