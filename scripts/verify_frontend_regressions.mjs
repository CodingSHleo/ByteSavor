import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const { searchRecipes } = await import('../bsapp/src/utils/recipe-search.js')

const recipes = [
  { title: '韭黄炒鸡蛋', ingredients: [{ name: '韭黄' }, { name: '鸡蛋' }], tags: ['quick'] },
  { title: '芹菜炒牛肉', ingredients: [{ name: '芹菜' }, { name: '牛肉' }], tags: ['high_protein'] },
  { title: '韭黄炒肉丝', ingredients: [{ name: '韭黄' }, { name: '猪肉' }], tags: ['quick'] },
  { title: '番茄炒蛋', ingredients: [{ name: '番茄' }, { name: '鸡蛋' }], tags: ['home'] },
  { title: '香辣牛肉', ingredients: [{ name: '牛肉' }, { name: '辣椒' }], tags: ['spicy', 'high_protein'] },
  { title: '清炒牛肉', ingredients: [{ name: '牛肉' }, { name: '西兰花' }], tags: ['light', 'high_protein'] },
]

assert.equal(searchRecipes(recipes, '韭黄炒蛋')[0]?.title, '韭黄炒鸡蛋')
assert.ok(searchRecipes(recipes, '炒蛋').some(r => r.title.includes('蛋')))
assert.ok(searchRecipes(recipes, '番茄炒鸡蛋').some(r => r.title === '番茄炒蛋'))

const beefChive = searchRecipes(recipes, '牛肉韭黄')
assert.ok(beefChive.length >= 2)
assert.ok(beefChive[0].title.includes('韭黄'))
assert.notEqual(beefChive[0].title, '芹菜炒牛肉')

assert.equal(searchRecipes(recipes, '牛肉', { preferences: ['清淡', '少油'] })[0].title, '清炒牛肉')

const communityVue = fs.readFileSync(path.join(root, 'bsapp/src/pages/community/community.vue'), 'utf8')
assert.ok(!communityVue.includes('ApiService.likePost('), 'community.vue must not call missing ApiService.likePost')
assert.ok(!communityVue.includes('ApiService.unlikePost('), 'community.vue must not call missing ApiService.unlikePost')

const homeVue = fs.readFileSync(path.join(root, 'bsapp/src/pages/home/home.vue'), 'utf8')
assert.ok(homeVue.includes('refresh: true'), 'home refresh flow must pass refresh: true')
assert.ok(homeVue.includes('recipeExplainChips(recipe)'), 'home recommendation cards must render explanation chips')
assert.ok(homeVue.includes('planner_source'), 'agent timeline must expose planner_source')
assert.ok(homeVue.includes('candidate_tools'), 'agent timeline must expose candidate_tools')
assert.ok(homeVue.includes('soft_judge'), 'agent timeline must render soft_judge events')
assert.ok(homeVue.includes('skillCategoryLabel'), 'agent timeline must label skill categories')

const exploreVue = fs.readFileSync(path.join(root, 'bsapp/src/pages/explore/explore.vue'), 'utf8')
assert.ok(exploreVue.includes('recipeExplainChips(item)'), 'explore recipe cards must render explanation chips')
assert.ok(exploreVue.includes('planRecipeFromExplore'), 'explore must keep add-to-meal-plan action')

const pagesJson = fs.readFileSync(path.join(root, 'bsapp/src/pages.json'), 'utf8')
assert.ok(pagesJson.includes('"iconPath"'), 'tabBar iconPath must exist')
assert.ok(pagesJson.includes('"selectedIconPath"'), 'tabBar selectedIconPath must exist')

const appVue = fs.existsSync(path.join(root, 'bsapp/src/App.vue'))
assert.ok(appVue, 'App.vue must exist for H5 build')

console.log('frontend regressions ok')
