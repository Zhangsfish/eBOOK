#!/usr/bin/env python3
"""Generate the checked-in Xcode project, without XcodeGen or third-party tools."""
from pathlib import Path
import argparse
import difflib
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]


def uid(label): return hashlib.sha1(label.encode()).hexdigest()[:24].upper()
def quoted(value): return json.dumps(str(value), ensure_ascii=False)


def generate():
    objects = {}
    def obj(label, isa, **fields):
        key = uid(label)
        objects[key] = {'isa': isa, **fields}
        return Ref(key)
    ordering = lambda path: path.relative_to(ROOT).as_posix()
    app_sources = sorted((ROOT / 'Sources').rglob('*.swift'), key=ordering)
    unit_sources = sorted((ROOT / 'Tests' / 'CoreTests').glob('*.swift'), key=ordering)
    ui_sources = sorted((ROOT / 'Tests' / 'UITests').glob('*.swift'), key=ordering)
    def file(path, file_type=None):
        rel = path.relative_to(ROOT).as_posix()
        return obj('file:' + rel, 'PBXFileReference', lastKnownFileType=file_type or ('sourcecode.swift' if path.suffix == '.swift' else 'text'), path=rel, sourceTree='<group>')
    all_files = []
    def sources(name, paths):
        builds = []
        for path in paths:
            ref = file(path); all_files.append(ref)
            builds.append(obj('build:' + name + path.relative_to(ROOT).as_posix(), 'PBXBuildFile', fileRef=ref))
        return obj('sources:' + name, 'PBXSourcesBuildPhase', buildActionMask='2147483647', files=builds, runOnlyForDeploymentPostprocessing='0')
    app_phase = sources('app', app_sources)
    unit_phase = sources('unit', unit_sources)
    ui_phase = sources('ui', ui_sources)
    def resources(name, paths):
        builds = []
        for path, kind in paths:
            ref = file(ROOT / path, kind); all_files.append(ref)
            builds.append(obj('resource:' + name + path, 'PBXBuildFile', fileRef=ref))
        return obj('resources:' + name, 'PBXResourcesBuildPhase', buildActionMask='2147483647', files=builds, runOnlyForDeploymentPostprocessing='0')
    app_resources = resources('app', [('Sources/eBOOK/PrivacyInfo.xcprivacy', 'text.xml'),
                                      ('Sources/eBOOK/Assets.xcassets', 'folder.assetcatalog')])
    unit_resources = resources('unit', [('Tests/Fixtures', 'folder'), ('.local-test-data/synthetic_long_gb18030.txt', 'text')])
    ui_resources = resources('ui', [])
    products = []
    def product(name, suffix, kind):
        ref = obj('product:' + name, 'PBXFileReference', explicitFileType=kind, includeInIndex='0', path=name + suffix, sourceTree='BUILT_PRODUCTS_DIR')
        products.append(ref); return ref
    app_product = product('eBOOK', '.app', 'wrapper.application')
    unit_product = product('EBookTests', '.xctest', 'wrapper.cfbundle')
    ui_product = product('EBookUITests', '.xctest', 'wrapper.cfbundle')
    group = obj('group:files', 'PBXGroup', children=all_files, name='Source and Tests', sourceTree='<group>')
    products_group = obj('group:products', 'PBXGroup', children=products, name='Products', sourceTree='<group>')
    main_group = obj('group:main', 'PBXGroup', children=[group, products_group], sourceTree='<group>')
    def configurations(label, settings):
        refs = []
        for name in ['Debug', 'Release']:
            values = dict(settings)
            values['SWIFT_OPTIMIZATION_LEVEL'] = '-Onone' if name == 'Debug' else '-O'
            if name == 'Debug':
                values['SWIFT_ACTIVE_COMPILATION_CONDITIONS'] = '$(inherited) DEBUG'
                values['ENABLE_TESTABILITY'] = 'YES'
                values['ONLY_ACTIVE_ARCH'] = 'YES'
            refs.append(obj('config:' + label + name, 'XCBuildConfiguration', buildSettings=values, name=name))
        return obj('configs:' + label, 'XCConfigurationList', buildConfigurations=refs, defaultConfigurationIsVisible='0', defaultConfigurationName='Release')
    project_config = configurations('project', {
        'SDKROOT': 'iphoneos', 'IPHONEOS_DEPLOYMENT_TARGET': '17.0', 'SWIFT_VERSION': '5.0',
        'CLANG_ENABLE_MODULES': 'YES', 'CLANG_ENABLE_OBJC_ARC': 'YES', 'GCC_C_LANGUAGE_STANDARD': 'gnu17',
        'SWIFT_STRICT_CONCURRENCY': 'minimal', 'DEBUG_INFORMATION_FORMAT': 'dwarf',
        'ENABLE_USER_SCRIPT_SANDBOXING': 'YES',
    })
    base = {'TARGETED_DEVICE_FAMILY': '1,2', 'PRODUCT_NAME': '$(TARGET_NAME)', 'CODE_SIGN_STYLE': 'Automatic'}
    app_config = configurations('app', {**base, 'PRODUCT_BUNDLE_IDENTIFIER': 'com.zhangsfish.ebook', 'PRODUCT_MODULE_NAME': 'EBook',
        'INFOPLIST_FILE': 'Sources/eBOOK/Info.plist', 'GENERATE_INFOPLIST_FILE': 'NO',
        'MARKETING_VERSION': '0.1.0', 'CURRENT_PROJECT_VERSION': '1',
        'ASSETCATALOG_COMPILER_APPICON_NAME': 'AppIcon',
        'OTHER_LDFLAGS': ['$(inherited)', '-lz'], 'LD_RUNPATH_SEARCH_PATHS': ['$(inherited)', '@executable_path/Frameworks'],
        'SUPPORTED_PLATFORMS': 'iphoneos iphonesimulator', 'SUPPORTS_MACCATALYST': 'NO'})
    unit_config = configurations('unit', {**base, 'PRODUCT_BUNDLE_IDENTIFIER': 'com.zhangsfish.ebook.tests',
        'GENERATE_INFOPLIST_FILE': 'YES', 'TEST_HOST': '$(BUILT_PRODUCTS_DIR)/eBOOK.app/eBOOK', 'BUNDLE_LOADER': '$(TEST_HOST)',
        'LD_RUNPATH_SEARCH_PATHS': ['$(inherited)', '@executable_path/Frameworks', '@loader_path/Frameworks']})
    ui_config = configurations('ui', {**base, 'PRODUCT_BUNDLE_IDENTIFIER': 'com.zhangsfish.ebook.uitests',
        'GENERATE_INFOPLIST_FILE': 'YES', 'TEST_TARGET_NAME': 'eBOOK'})
    app_target = obj('target:app', 'PBXNativeTarget', buildConfigurationList=app_config, buildPhases=[app_phase, app_resources], buildRules=[], dependencies=[], name='eBOOK', productName='eBOOK', productReference=app_product, productType='com.apple.product-type.application')
    proxy = obj('proxy:app', 'PBXContainerItemProxy', containerPortal=Ref(uid('project')), proxyType='1', remoteGlobalIDString=app_target, remoteInfo='eBOOK')
    def test_target(name, phase, resource_phase, config, output):
        dependency = obj('dependency:' + name, 'PBXTargetDependency', target=app_target, targetProxy=proxy)
        return obj('target:' + name, 'PBXNativeTarget', buildConfigurationList=config, buildPhases=[phase, resource_phase], buildRules=[], dependencies=[dependency], name=name, productName=name, productReference=output, productType='com.apple.product-type.bundle.' + ('ui-testing' if name == 'EBookUITests' else 'unit-test'))
    unit_target = test_target('EBookTests', unit_phase, unit_resources, unit_config, unit_product)
    ui_target = test_target('EBookUITests', ui_phase, ui_resources, ui_config, ui_product)
    project = obj('project', 'PBXProject', attributes={'BuildIndependentTargetsInParallel': 'YES', 'LastUpgradeCheck': '1640', 'TargetAttributes': {
        str(app_target): {'CreatedOnToolsVersion': '16.4'}, str(unit_target): {'CreatedOnToolsVersion': '16.4', 'TestTargetID': app_target}, str(ui_target): {'CreatedOnToolsVersion': '16.4', 'TestTargetID': app_target}}},
        buildConfigurationList=project_config, compatibilityVersion='Xcode 14.0', developmentRegion='zh_CN', hasScannedForEncodings='0', knownRegions=['zh_CN', 'en', 'Base'], mainGroup=main_group, productRefGroup=products_group, projectDirPath='', projectRoot='', targets=[app_target, unit_target, ui_target])
    def render(value, level=0):
        if isinstance(value, Ref): return str(value)
        if isinstance(value, dict):
            return '{\n' + ''.join('  ' * (level + 1) + quoted(k) + ' = ' + render(v, level + 1) + ';\n' for k, v in value.items()) + '  ' * level + '}'
        if isinstance(value, list): return '(' + ', '.join(render(v, level) for v in value) + ')'
        return quoted(value)
    content = '// !$*UTF8*$!\n' + render({'archiveVersion': '1', 'classes': {}, 'objectVersion': '56', 'objects': objects, 'rootObject': project}) + '\n'
    def buildable(ref, name, suffix):
        return f'<BuildableReference BuildableIdentifier="primary" BlueprintIdentifier="{ref}" BuildableName="{name}{suffix}" BlueprintName="{name}" ReferencedContainer="container:eBOOK.xcodeproj"/>'
    app_xml = buildable(app_target, 'eBOOK', '.app')
    tests_xml = ''.join(f'<TestableReference skipped="NO">{buildable(ref, name, ".xctest")}</TestableReference>' for ref, name in [(unit_target, 'EBookTests'), (ui_target, 'EBookUITests')])
    scheme = f'''<?xml version="1.0" encoding="UTF-8"?>
<Scheme LastUpgradeVersion="1640" version="1.3">
<BuildAction parallelizeBuildables="YES" buildImplicitDependencies="YES"><BuildActionEntries><BuildActionEntry buildForTesting="YES" buildForRunning="YES" buildForProfiling="YES" buildForArchiving="YES" buildForAnalyzing="YES">{app_xml}</BuildActionEntry></BuildActionEntries></BuildAction>
<TestAction buildConfiguration="Debug" selectedDebuggerIdentifier="Xcode.DebuggerFoundation.Debugger.LLDB" selectedLauncherIdentifier="Xcode.IDEFoundation.Launcher.LLDB" shouldUseLaunchSchemeArgsEnv="YES"><Testables>{tests_xml}</Testables></TestAction>
<LaunchAction buildConfiguration="Debug" selectedDebuggerIdentifier="Xcode.DebuggerFoundation.Debugger.LLDB" selectedLauncherIdentifier="Xcode.IDEFoundation.Launcher.LLDB" launchStyle="0" useCustomWorkingDirectory="NO" ignoresPersistentStateOnLaunch="NO" debugDocumentVersioning="YES" debugServiceExtension="internal" allowLocationSimulation="YES"><BuildableProductRunnable runnableDebuggingMode="0">{app_xml}</BuildableProductRunnable></LaunchAction>
<ProfileAction buildConfiguration="Release" shouldUseLaunchSchemeArgsEnv="YES" savedToolIdentifier="" useCustomWorkingDirectory="NO" debugDocumentVersioning="YES"><BuildableProductRunnable runnableDebuggingMode="0">{app_xml}</BuildableProductRunnable></ProfileAction>
<AnalyzeAction buildConfiguration="Debug"/>
<ArchiveAction buildConfiguration="Release" revealArchiveInOrganizer="YES"/>
</Scheme>
'''
    return {'eBOOK.xcodeproj/project.pbxproj': content, 'eBOOK.xcodeproj/xcshareddata/xcschemes/eBOOK.xcscheme': scheme}


class Ref(str): pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    for relative, content in generate().items():
        path = ROOT / relative
        if args.check:
            previous = path.read_text(encoding='utf-8') if path.exists() else ''
            if previous != content:
                print(''.join(list(difflib.unified_diff(previous.splitlines(True), content.splitlines(True), fromfile='checked-in', tofile='generated'))[:80]))
                raise SystemExit(f'Project is stale: {relative}')
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding='utf-8', newline='\n')
    print('Xcode project is current.' if args.check else 'Generated eBOOK.xcodeproj (no external tools).')


if __name__ == '__main__': main()
